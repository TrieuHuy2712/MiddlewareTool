import sys

from PyQt5 import QtWidgets

from ActionGUIMain import ActionMainGui
from GUIMain import Ui_MainWindow
from src.Enums import SapoShop
from src.Factory.OrderFactory import OrderFactory, OrderAutoFactory
from src.utils import get_item_information


def main():
    app = QtWidgets.QApplication(sys.argv)
    # main_window = QtWidgets.QMainWindow()
    # ex = Ui_MainWindow()
    # ex.setupUi(main_window)
    """Call action method to create instance value"""
    main_window = ActionMainGui()
    main_window.show()
    sys.exit(app.exec_())


def application(factory: OrderFactory):

    # Run with sapo
    # orderTest = factory.create_sapo_order(SapoShop.QuocCoQuocNghiepShop)
    # orderTest.get_orders(["461155164021256", "578480329448393218", "459022254934695"])

    # Run with website
    orderTest = factory.create_web_order()
    orderTest.get_orders_by_search(["61807317"])


if __name__ == '__main__':
    sys.tracebacklimit = 0
    main()
    # get_item_information()
    # application(OrderAutoFactory())
