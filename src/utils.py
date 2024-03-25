import json
import logging
import os
import time
from datetime import datetime, timedelta
from functools import lru_cache
import logging.handlers

import pandas
import yaml
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.InputProduct import InputProduct
from src.Singleton.AppConfig import AppConfig


def set_up_logger(logger_id):
    """
    Sets up a logger with required file handler and formatting.


    :param logger_id:
    :return:
    """
    logger = logging.getLogger(logger_id)
    logger.setLevel(logging.INFO)

    # Add the log message handler to the logger
    if logger.hasHandlers():
        logger.handlers.clear()

    exp_handler = logging.handlers.RotatingFileHandler(
        logger_id + '.log', maxBytes=3000000, backupCount=5)
    logger.addHandler(exp_handler)

    fmr = logging.Formatter(
        '{"Time": %(asctime)s, "Level": "%(levelname)s", "Message": %(message)s}'
    )
    logger.handlers[0].setFormatter(fmr)

    return logger


@lru_cache(maxsize=128)
def get_value_of_config(config: str) -> str:
    """

    :param config:
    :raises KeyError
    :return:
    """
    try:
        return get_user_env(config)
    except KeyError:
        try:
            with open('conf.yml', 'r') as f:
                data = yaml.safe_load(f)
                return data[config]
        except Exception as e:
            raise KeyError(f'Config is missing {config}')


def get_user_env(name) -> str:
    """
    :returns environment variable value. None if does not exist.
    """
    val = os.getenv(name)
    if val is None:
        raise KeyError(name)
    return val


def attempt_check_exist_by_xpath(xpath, max_attempt=5):
    attempt = 0
    while attempt < max_attempt:
        if not check_element_exist(xpath):
            attempt = attempt + 1
        else:
            time.sleep(2)
            return
    raise NoSuchElementException(msg=f"Cannot find element at XPath {xpath}")


def attempt_check_can_clickable_by_xpath(xpath, max_attempt=5):
    attempt = 0
    while attempt < max_attempt:
        if not check_element_can_clickable(xpath):
            attempt = attempt + 1
        else:
            time.sleep(2)
            return
    raise NoSuchElementException(msg=f"Cannot clickable element at XPath {xpath}")


# Wait for the presence of a specific element on the page
def check_element_exist(element, type: By = By.XPATH, timeout=10):
    try:
        element_present = EC.presence_of_element_located((type, element))
        WebDriverWait(AppConfig().chrome_driver, timeout).until(element_present)
        return True
    except TimeoutException:
        return False


def check_element_can_clickable(element, type: By = By.XPATH, timeout=10):
    try:
        element_present = EC.element_to_be_clickable((type, element))
        WebDriverWait(AppConfig().chrome_driver, timeout).until(element_present)
        return True
    except TimeoutException:
        return False


def set_default_if_none(input_data, default_value=''):
    return default_value if input_data is None else input_data


def get_current_date_time(format_time='%d/%m/%d %H:%M:%S %p', date_diff=0):
    # dd/MM/yyyy hh:mm:ss AP
    return datetime.now() + timedelta(days=date_diff)


def get_money_format(money):
    try:
        return "{:,.0f}".format(money)
    except:
        return money


def get_item_information() -> list[InputProduct]:
    excel_data_df = pandas.read_excel('ITEM_INFORMATION.xlsx', sheet_name='Sheet1', skiprows=1)

    # Group columns
    grouped = excel_data_df.groupby(['ITEM_ID','ITEM_NAME','ITEM_QUANTITY']).agg(list)
    convert_to_json = grouped.to_json(orient='index', indent=4)

    data = json.loads(convert_to_json)

    # Initialize an empty list for the transformed items
    transformed_data = []

    # Process each item in the original data
    for key, value in data.items():
        # Split the key into its components and strip unnecessary characters
        item_id, item_name, item_quantity = eval(key)

        # Extract products data
        products = []
        for i in range(len(value["PRODUCT_ID"])):
            product = {
                "Product_Id": value["PRODUCT_ID"][i],
                "Product_Name": value["PRODUCT_NAME"][i],
                "Product_Quantity": value["PRODUCT_QUANTITY"][i],
                "Unit": value["UNIT "][i].strip(),
                "Price_not_VAT": value["PRICE_NOT_VAT"][i]
            }
            products.append(product)

        # Create a new dictionary for the transformed item
        transformed_item = {
            "Item_Id": item_id,
            "Item_Name": item_name,
            "Item_Quantity": item_quantity,
            "Product": products
        }

        # Append the transformed item to the list
        transformed_data.append(InputProduct.from_dict(transformed_item))
    # Convert the list of transformed items back to a JSON string
    return transformed_data