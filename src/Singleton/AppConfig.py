import chromedriver_autoinstaller
from selenium import webdriver


class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            chromedriver_autoinstaller.install()
            """Set driver """
            cls._instance.chrome_driver = webdriver.Chrome()
        return cls._instance

    def get_chrome_driver(self):
        return self.chrome_driver

    @classmethod
    def destroy_instance(cls):
        if cls._instance:
            cls._instance.chrome_driver.quit()
            cls._instance = None
