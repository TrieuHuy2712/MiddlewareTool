import time
from abc import ABC, abstractmethod

from selenium.common import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.Exceptions import OrderError
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import set_up_logger, get_value_of_config, attempt_check_exist_by_xpath, \
    attempt_check_can_clickable_by_xpath, check_element_can_clickable, check_element_not_exist


class AutomationMisaOrder(ABC):
    def __init__(self, orders: list[Order]):
        self.orders = orders
        self.logging = set_up_logger("Middleware_Tool")
        self.driver = AppConfig().chrome_driver
        self.missing_orders = []
        self.handle_orders = []
        self.attempt = 1

    @abstractmethod
    def send_orders_to_misa(self):
        pass

    def _get_list_missing_orders(self) -> list[Order]:
        return [o for o in self.orders if o.code not in self.handle_orders]

    def _escape_current_invoice(self):
        # Check balance modal
        if not check_element_not_exist('//span[contains(@id, "idMessage") and contains(text(), "Tổng tiền thuế GTGT")]', timeout=30):
            yes_button_xpath = '//span[contains(@id, "idMessage") and contains(text(), "Tổng tiền thuế GTGT")]/ancestor::div[@class="ms-message-box--content"]/div[@class="mess-footer"]//button/div[contains(text(),"Có")]'
            self.driver.find_element(By.XPATH, yes_button_xpath).click()

        # Escape
        attempt_check_can_clickable_by_xpath('//div[contains(@class,"close-btn header")]')
        self.driver.find_element(By.XPATH, '//div[contains(@class,"close-btn header")]').click()

        # Check if existed after unit time
        if not check_element_not_exist('//div[@class="title"]', timeout=30):
            self._escape_current_invoice()

    def _open_website(self):
        url = get_value_of_config("misa_url")
        self.driver.get(url)

    def _go_to_sale_page(self):
        # Click a tag Sale Order
        sa_xpath = '//div[text()="Bán hàng"]/parent::a'
        self._action_click_with_xpath_(sa_xpath)

        # Click invoice menu
        invoice_xpath = '(//div[normalize-space(text())="Hóa đơn"])[1]'
        self._action_click_with_xpath_(invoice_xpath)

        # Click add invoice
        add_invoice_xpath = '//div[normalize-space(text())="Thêm hóa đơn"]/parent::button'
        self._action_click_with_xpath_(add_invoice_xpath)

        # Click right collapse
        tooltip_collapse_xpath = '//div[@class ="collapse-btn right-collapse"]'
        is_available = check_element_can_clickable(tooltip_collapse_xpath, By.XPATH)
        if is_available:
            self.driver.find_element(By.XPATH, tooltip_collapse_xpath).click()

        # Click option discount
        discount_dropdown_xpath = '//div[text()="Chiết khấu"]/parent::div//div[@class="btn-dropdown"]'
        self._action_click_with_xpath_(discount_dropdown_xpath)

        discount_total_option_xpath = '//div[@title="Theo số tiền trên tổng hóa đơn"]'
        self._action_click_with_xpath_(discount_total_option_xpath)

    def _go_to_warehouse_page(self):
        # Click warehouse tag
        warehouse_xpath = '//div[text()="Kho"]/parent::a'
        self._action_click_with_xpath_(warehouse_xpath)

        # Click export warehouse
        export_warehouse_xpath = '(//div[normalize-space(text())="Xuất kho"])[1]'
        self._action_click_with_xpath_(export_warehouse_xpath)

        # Click add button
        add_invoice_xpath = '//div[normalize-space(text())="Thêm"]/parent::button'
        self._action_click_with_xpath_(add_invoice_xpath)

    def _authentication(self):
        # Input email
        email_xpath = '//input[@name="username"]'
        attempt_check_exist_by_xpath(email_xpath)
        self.driver.find_element(By.XPATH, email_xpath).send_keys(get_value_of_config("misa_login"))

        # Input password
        password_xpath = '//input[@name="pass"]'
        attempt_check_exist_by_xpath(password_xpath)
        self.driver.find_element(By.XPATH, password_xpath).send_keys(get_value_of_config("misa_password"))

        # Click login button
        button_xpath = '//button[@objname="jBtnLogin"]'
        attempt_check_can_clickable_by_xpath(button_xpath)
        self.driver.find_element(By.XPATH, button_xpath).click()

        # Check_current_session
        session_xpath = '//div[text()="Tiếp tục đăng nhập"]/parent::button'
        try:
            attempt_check_exist_by_xpath(session_xpath, max_attempt=2)
            self.driver.find_element(By.XPATH, session_xpath).click()
        except NoSuchElementException as e:
            self.logging.info(msg="No users use this account")
        finally:
            return

    def _go_to_internal_accounting_data_page(self):
        current_db_name = get_value_of_config('header_current_db_name')
        db_button_xpath = '//div[@class="header-current-db-name"]'
        attempt_check_exist_by_xpath(db_button_xpath)
        if self.driver.find_element(By.XPATH, db_button_xpath).text.strip() != current_db_name.strip():
            self.driver.find_element(By.XPATH, db_button_xpath).click()
            table_db_button = f'//p[@title="{current_db_name}"]//ancestor::table'
            attempt_check_can_clickable_by_xpath(table_db_button)
            self.driver.find_element(By.XPATH, table_db_button).click()
            attempt_check_exist_by_xpath(
                '//div[@class="title-branch"]/following-sibling::div/div[@class="title-header"]')

    def _action_click_with_xpath_(self, xpath):
        try:
            attempt_check_can_clickable_by_xpath(xpath)
            self.driver.find_element(By.XPATH, xpath).click()
        except ElementClickInterceptedException as e:
            element = self.driver.find_element(By.XPATH, xpath)
            ActionChains(self.driver).move_to_element(element).click().perform()
        except NoSuchElementException as e:
            raise OrderError(message=f"No such element. {e}")
        except Exception as e:
            raise OrderError(message=f"Cannot click element. {e}")