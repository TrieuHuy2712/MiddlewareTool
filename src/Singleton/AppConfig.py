import threading

import chromedriver_autoinstaller
from selenium import webdriver


class AppConfig:
    _thread_local = threading.local()

    def __init__(self):
        chromedriver_autoinstaller.install()

    @classmethod
    def get_chrome_driver(cls):
        """Lấy WebDriver cho thread hiện tại, nếu chưa có thì tạo mới."""
        if not hasattr(cls._thread_local, "chrome_driver"):
            options = webdriver.ChromeOptions()
            cls._thread_local.chrome_driver = webdriver.Chrome(options=options)
        return cls._thread_local.chrome_driver

    @classmethod
    def destroy_instance(cls):
        """Đóng WebDriver của thread hiện tại nếu tồn tại."""
        if hasattr(cls._thread_local, "chrome_driver"):
            cls._thread_local.chrome_driver.quit()
            del cls._thread_local.chrome_driver  # Xóa WebDriver khỏi thread-local storage
