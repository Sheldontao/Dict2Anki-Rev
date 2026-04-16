import json
import logging
import os
import threading
import time

import requests
from urllib3 import Retry
from itertools import chain
from .misc import ThreadPool, SimpleWord
from . import utils
from requests.adapters import HTTPAdapter
from .constants import VERSION, VERSION_CHECK_API
from aqt.qt import QObject, pyqtSignal, QThread
from .repair_logic import compute_missing_fields


class WorkerManager:
    """Small helper to reduce repeated Qt worker wiring."""

    def __init__(self, thread: QThread):
        self.thread = thread

    def start(self, worker: QObject, done_signal_name: str):
        worker.moveToThread(self.thread)
        start_signal = getattr(worker, 'start')
        done_signal = getattr(worker, done_signal_name)
        done_signal.connect(worker.deleteLater)
        start_signal.connect(worker.run)
        start_signal.emit()


class VersionCheckWorker(QObject):
    haveNewVersion = pyqtSignal(str, str)
    finished = pyqtSignal()
    start = pyqtSignal()
    logger = logging.getLogger('dict2Anki.workers.UpdateCheckWorker')

    def run(self):
        currentThread = QThread.currentThread()
        if currentThread.isInterruptionRequested():
            self.finished.emit()
            return
        try:
            self.logger.info('检查新版本')
            rsp = requests.get(VERSION_CHECK_API, timeout=20).json()
            version = rsp['tag_name']
            changeLog = rsp['body']
            if version != VERSION:
                self.logger.info(f'检查到新版本:{version}--{changeLog.strip()}')
                self.haveNewVersion.emit(version.strip(), changeLog.strip())
            else:
                self.logger.info(f'当前为最新版本:{VERSION}')
        except Exception as e:
            self.logger.error(f'版本检查失败{e}')

        finally:
            self.finished.emit()


class LoginStateCheckWorker(QObject):
    start = pyqtSignal()
    logSuccess = pyqtSignal(str)
    logFailed = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, checkFn, cookie):
        super().__init__()
        self.checkFn = checkFn
        self.cookie = cookie

    def run(self):
        try:
            loginState = self.checkFn(self.cookie)
            if loginState:
                self.logSuccess.emit(json.dumps(self.cookie))
            else:
                self.logFailed.emit()
        finally:
            self.finished.emit()


class RemoteWordFetchingWorker(QObject):
    start = pyqtSignal()
    tick = pyqtSignal()
    setProgress = pyqtSignal(int)
    done = pyqtSignal()
    doneThisGroup = pyqtSignal(list)
    logger = logging.getLogger('dict2Anki.workers.RemoteWordFetchingWorker')

    def __init__(self, selectedDict, selectedGroups: [tuple]):
        super().__init__()
        self.selectedDict = selectedDict
        self.selectedGroups = selectedGroups

    def run(self):
        currentThread = QThread.currentThread()

        def _pull(*args):
            if currentThread.isInterruptionRequested():
                return
            wordPerPage = self.selectedDict.getWordsByPage(*args)
            self.tick.emit()
            return wordPerPage

        for groupName, groupId in self.selectedGroups:
            totalPage = self.selectedDict.getTotalPage(groupName, groupId)
            self.setProgress.emit(totalPage)
            with ThreadPool(max_workers=3) as executor:
                for i in range(totalPage):
                    executor.submit(_pull, i, groupName, groupId)
            remoteWordList = list(chain(*[ft for ft in executor.result]))
            self.doneThisGroup.emit(remoteWordList)

        self.done.emit()


class QueryWorker(QObject):
    start = pyqtSignal()
    tick = pyqtSignal()
    thisRowDone = pyqtSignal(int, dict)
    thisRowFailed = pyqtSignal(int)
    allQueryDone = pyqtSignal()
    logger = logging.getLogger('dict2Anki.workers.QueryWorker')

    def __init__(self, wordList: [(SimpleWord, int)], api, congest_per_minute=60):
        super().__init__()
        self.wordList = wordList
        self.api = api
        self.congest_per_minute = max(1, int(congest_per_minute or 60))

    def run(self):
        currentThread = QThread.currentThread()
        api_instance = self.api # Get the API instance once
        total = len(self.wordList)
        stats = {
            'success': 0,
            'failed': 0,
            'with_image': 0,
            'without_image': 0,
            'with_definition_en': 0,
            'without_definition_en': 0,
        }
        stats_lock = threading.Lock()

        def _query(word: SimpleWord, row, api_obj): # _query now accepts api_obj
            if currentThread.isInterruptionRequested():
                return
            queryResult = api_obj.query(word) # Use api_obj
            if queryResult:
                missing_fields = compute_missing_fields(queryResult)
                queryResult['_missing_fields'] = missing_fields

                if not queryResult.get('AmEPhonetic') and not queryResult.get('BrEPhonetic'):
                    self.logger.warning(f'[{word}] Phonetic information not found in query result: {queryResult}')
                has_image = bool(queryResult.get('image'))
                has_definition_en = bool(queryResult.get('definition_en'))
                with stats_lock:
                    stats['success'] += 1
                    stats['with_image' if has_image else 'without_image'] += 1
                    stats['with_definition_en' if has_definition_en else 'without_definition_en'] += 1

                self.logger.info(
                    f"查询成功: {word} -- image={'Y' if has_image else 'N'}, "
                    f"definition_en={'Y' if has_definition_en else 'N'}, "
                    f"missing={','.join(missing_fields) if missing_fields else 'none'}"
                )
                self.logger.debug(f'查询详情: {word} -- {queryResult}')
                self.thisRowDone.emit(row, queryResult)
            else:
                self.logger.warning(f'查询失败: {word}')
                with stats_lock:
                    stats['failed'] += 1
                self.thisRowFailed.emit(row)

            self.tick.emit()
            return queryResult

        with ThreadPool(max_workers=3) as executor:
            for (word, row) in self.wordList:
                executor.submit(_query, word, row, api_instance) # Pass api_instance
                # Soft rate-limit requests to avoid upstream throttling.
                time.sleep(60.0 / self.congest_per_minute)

        self.logger.info(
            '查询完成汇总: '
            f"total={total}, success={stats['success']}, failed={stats['failed']}, "
            f"image={stats['with_image']}/{stats['success']}, "
            f"definition_en={stats['with_definition_en']}/{stats['success']}"
        )

        self.allQueryDone.emit()


class AssetDownloadWorker(QObject):
    """Asset (Image and Audio) download worker"""
    start = pyqtSignal()
    tick = pyqtSignal()
    itemDone = pyqtSignal(str, str)
    done = pyqtSignal()
    logger = logging.getLogger('dict2Anki.workers.AudioDownloadWorker')
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    def __init__(self, target_dir, images: [tuple], audios: [tuple], overwrite=False, max_retry=3):
        super().__init__()
        self.target_dir = target_dir
        self.images = images
        self.audios = audios
        self.overwrite = overwrite
        self.max_retry = max_retry

    def run(self):
        currentThread = QThread.currentThread()

        def __download_with_retry(filename, url):
            success = False
            final_status = 'download-failed'
            for i in range(self.max_retry):
                ok, status = __download(filename, url)
                final_status = status
                if ok:
                    success = True
                    break
                if currentThread.isInterruptionRequested():
                    success = False
                    final_status = 'download-failed'
                    break
                self.logger.info(f"Retrying {i+1} time...")
            if success:
                self.tick.emit()
                self.itemDone.emit(filename, final_status)
            else:
                self.itemDone.emit(filename, 'download-failed')
                self.logger.error(f"FAILED to download {filename} after retrying {self.max_retry} times!")
                self.logger.info("----------------------------------")

        def __download(fileName, url) -> (bool, str):
            """Do NOT call this method directly. Use `__download_with_retry` instead."""
            filepath = os.path.join(self.target_dir, fileName)
            tmp_filepath = filepath + '.part'
            try:
                if currentThread.isInterruptionRequested():
                    return False, 'download-failed'
                self.logger.info(f'Downloading {fileName}...')
                is_image = fileName.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))
                is_audio = fileName.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))
                # file already exists
                if os.path.exists(filepath):
                    if not self.overwrite:
                        if is_image and utils.is_image_file_broken(f'<img src="{fileName}">', self.target_dir):
                            self.logger.warning(f"Existing image looks broken, redownloading: {fileName}")
                        else:
                            self.logger.info(f"[SKIP] {fileName} already exists")
                            return True, 'skipped'
                    else:
                        self.logger.warning(f"Overwriting file {fileName}")

                r = self.session.get(url, stream=True, timeout=20)
                r.raise_for_status()

                content_type = (r.headers.get('Content-Type') or '').lower()

                if is_image and not content_type.startswith('image/'):
                    self.logger.warning(f"Unexpected content type for image {fileName}: {content_type}")
                    return False, 'download-failed'
                if is_audio and not (
                    content_type.startswith('audio/')
                    or 'octet-stream' in content_type
                    or content_type == ''
                ):
                    self.logger.warning(f"Unexpected content type for audio {fileName}: {content_type}")
                    return False, 'download-failed'

                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)

                with open(tmp_filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if currentThread.isInterruptionRequested():
                            raise InterruptedError('Download interrupted by thread shutdown')
                        if chunk:
                            f.write(chunk)

                os.replace(tmp_filepath, filepath)
                self.logger.info(f'[OK] {fileName} 下载完成')
                self.logger.info("----------------------------------")
                return True, 'filled'
            except Exception as e:
                self.logger.warning(f'下载{fileName}:{url}异常: {e}')
                try:
                    if os.path.exists(tmp_filepath):
                        os.remove(tmp_filepath)
                except Exception:
                    pass
                return False, 'download-failed'

        with ThreadPool(max_workers=3) as executor:
            # download images
            for fileName, url in self.images:
                executor.submit(__download_with_retry, fileName, url)
            # download audios
            for fileName, url in self.audios:
                executor.submit(__download_with_retry, fileName, url)
        self.done.emit()

    @classmethod
    def close(cls):
        cls.session.close()
