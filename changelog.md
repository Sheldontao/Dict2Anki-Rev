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
   - **原因**：与第2点相同，修补了“下载缺失音频图片”这一特殊任务完成时的线程回收逻辑，确保线程生命周期管理的一致性和安全性。
