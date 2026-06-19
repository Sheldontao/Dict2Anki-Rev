# Changelog

## [7.3.0] - 2026-06-19

### Added
- **Per-group model assignment**: the group selection dialog (the popup that appears when fetching words from a dictionary) now shows a table with three columns — `[Sync checkbox, Group name, Model dropdown]`. Users can pick `Dict2Anki` or `Dict2Anki-Listening` for each source group. Selection is persisted in a new `groupModel` config field (mapping group name → model name). When syncing, each word uses the model assigned to its source group. Words with no explicit assignment fall back to `Dict2Anki`.

### Changed
- `addon/UIForm/wordGroup.py`: replaced `QListWidget` with `QTableWidget` to add the model column.
- `addon/workers.py`: `RemoteWordFetchingWorker.doneThisGroup` now emits `(groupName, words)` so the receiver can tag words with their source group.
- `addon/addonWindow.py`: new `remoteWordSourceGroup` dict tracks the source group for each fetched word. The sync flow looks up `groupModel[source_group]` per word and uses the corresponding model object when calling `addNoteToDeck`.

## [7.2.0] - 2026-06-19

### Changed
- **Hardcoded card templates**: replaced the previous FieldGroup-based dynamic template generation with two hardcoded model template sets (the original Dict2Anki styling and a new Dict2Anki-Listening typing card). Each model now has a single card type with its own CSS.
  - `Dict2Anki` model → card type `Forward` using the standard term → recall-definition layout with hint-revealed definitions and per-sentence audio icons. New CSS in `addon/constants.py:DICT2ANKI_CSS`.
  - `Dict2Anki-Listening` model → card type `Listening` using `{{type:term}}` typing card with hidden images / phrases / sentences that reveal on the back via `.back-card .hide-on-front { display: table-cell }`. New CSS in `addon/constants.py:LISTENING_CSS`.
  - Both models are created/reset automatically on sync.
- **Removed FieldGroup**: the dynamic template-toggling class (`addon/constants.py`) is no longer needed and was deleted. The sync flow no longer calls `getFieldGroup()`. Empty fields are handled by Anki's built-in `{{#field}}{{/field}}` conditionals in the new templates.
- **Removed Backwards template button**: the "Add/Delete Backwards Template" button in the Danger Zone group has been removed — the Backwards concept is replaced by the always-on `Dict2Anki-Listening` model.
- **Updated Check Card Templates**: now iterates over both `Dict2Anki` and `Dict2Anki-Listening` models, optionally removing stale card templates and resetting the per-model CSS.
- Added `tests/test_hardcoded_templates.py` (13 tests) pinning the structure of the two hardcoded templates and CSS.

## [7.1.1] - 2026-06-19

### Changed
- Eudic `pronunciations` parser (`addon/queryApi/eudict.py`) now uses a strict `startswith(('http://', 'https://'))` scheme check when deciding whether a phonetic `data-rel` needs the `https://api.frdic.com/api/v2/speech/speakweb?` prefix. Previously a substring match (`'http' not in url`) was used; the new check aligns with the sentence-speech pattern at `addon/queryApi/eudict.py:44` and removes the edge case where a `data-rel` that happens to contain the literal substring `http` (but is not actually a URL) could be kept verbatim. No user-visible behavior change for known Eudic data shapes (verified against `ulterior/*.html` — only query-string and full-URL shapes are present in the wild).
- Added regression tests under `tests/test_eudic_pronunciations.py` and `tests/test_youdao_pronunciations.py` pinning the URL-only contract for `BrEPron` / `AmEPron` across both parsers — populated values must match `^https?://` and must never contain Anki's `[sound:` local-media reference syntax.

## [Unreleased] - 2026-03-24

### Fixed
- **崩溃问题修复 (Crash Fix)**: 修复了在 Anki 插件关闭或同步结束时，因后台线程（QThread）未被彻底销毁而导致 `Fatal: QThread: Destroyed while thread is still running` (SIGABRT) 的严重崩溃问题。此问题在 macOS 配合 Python 3.13 环境下尤为容易触发。

### Changed
**修改文件：`addon/addonWindow.py`**

1. **优化了 `closeEvent`（主窗口关闭事件）的线程退出逻辑**：
   - 为 `workerThread`、`updateCheckThead` 和 `assetDownloadThread` 在调用 `.quit()` 和 `.wait()` 之前，均增加了 `.requestInterruption()` 的调用。
   - **原因**：单独使用 `.quit()` 只能退出线程的事件循环，但如果线程内部正在执行耗时任务（如正在进行 requests 网络请求循环），线程并不会立即结束。增加 `.requestInterruption()` 可以安全地向线程内部发送中断信号（`workers.py` 内部已通过 `isInterruptionRequested()` 监听了此信号），配合 `.wait()` 保证主线程阻塞直到后台子线程安全且彻底地退出，避免对象销毁时子线程仍在运行导致报错。

2. **完善了 `on_assetsDownloadDone` 方法**：
   - 在调用 `self.assetDownloadThread.quit()` 之后增加了 `self.assetDownloadThread.wait()`。
   - **原因**：下载任务完成后需要回收线程，增加 `.wait()` 以阻塞确保线程完全终止，防止资源竞争（Race Condition）和僵尸线程问题。

3. **完善了 `__on_assetsDownloadDone_DownloadMissingAssets` 方法**：
   - 在调用 `self.assetDownloadThread.quit()` 之后同样增加了 `self.assetDownloadThread.wait()`。
   **修改文件：`addon/misc.py`**

   1. **重构 `ThreadPool.wait_complete`**：
      - 之前调用 `self._q.join()` 会无限制地阻塞当前 Qt 线程直到所有原生 Python 线程（`threading.Thread`）完成全部网络请求。
      - **原因**：如果关闭窗口时正好有数十个单词等待查询，由于阻塞，主线程无响应，导致 `QThread.wait()` 超时并导致后续析构时崩溃。现在通过修改为轮询模式并在检测到 `QThread` 传来 `isInterruptionRequested` 信号时主动清空队列并跳出，实现线程池任务的快速中止与安全释放。

   **修改文件：`addon/workers.py`**

   1. **修复 `AssetDownloadWorker` 中错误的同步调用**：
      - 将 `executor.submit(__download_with_retry(fileName, url))` 修改为 `executor.submit(__download_with_retry, fileName, url)`。
      - **原因**：之前的写法导致第一个图片下载操作在提交给线程池之前就在当前主工作线程内被同步执行了，这破坏了并发机制，还会导致关闭程序时无法及时响应中断请求。
