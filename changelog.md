# Changelog

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
