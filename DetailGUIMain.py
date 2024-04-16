from datetime import datetime

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem

import GUIDetail
from src.Model.Order import Order
from src.utils import get_money_format


class DetailGUIMain(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.detail_gui = GUIDetail.Ui_MainWindow()
        self.detail_gui.setupUi(self)
        self.add_default_header()

    def add_default_header(self):
        table_headers = ["STT", "SKU", "Tên hàng hóa dịch vụ", "Đơn vị tính", "Số lượng", "Đơn giá", "Thành tiền"]
        self.detail_gui.tableWidget.setColumnCount(len(table_headers))
        self.detail_gui.tableWidget.setHorizontalHeaderLabels(table_headers)
        # Table header
        for index, ele in enumerate(table_headers):
            self.detail_gui.tableWidget.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)

    def get_order_detail(self, order: Order):
        self.detail_gui.tbBuyer.setText(f"{order.customer_data.name}")
        self.detail_gui.tbAddress.setText(f"Khách hàng lẻ không lấy hóa đơn (Bán hàng qua {order.source_name})")
        self.detail_gui.tbPaymentMethod.setText("Tiền mặt/Chuyển khoản")
        # sub_total
        sub_total = 0.0

        # tax_amount
        tax_amount = sum(float(item.tax_amount) for item in order.order_line_items)
        self.detail_gui.lbVATAmount.setText(get_money_format(float(tax_amount)))

        # Total Payment
        self.detail_gui.lbTotalPayment_2.setText(get_money_format(float(order.total)))

        created_date = datetime.strptime(order.created_on, '%Y-%m-%dT%H:%M:%SZ')

        current_row = 0
        self.detail_gui.tableWidget.setRowCount(len(order.order_line_items)+5)
        for item in order.order_line_items:
            if item.is_composite:
                for it in item.composite_item_domains:
                    self.detail_gui.tableWidget.setItem(current_row, 0, QTableWidgetItem(str(current_row + 1)))
                    self.detail_gui.tableWidget.setItem(current_row, 1, QTableWidgetItem(str(it.sku)))
                    self.detail_gui.tableWidget.setItem(current_row, 2, QTableWidgetItem(it.product_name))
                    self.detail_gui.tableWidget.setItem(current_row, 3, QTableWidgetItem(it.unit))
                    self.detail_gui.tableWidget.setItem(current_row, 4, QTableWidgetItem(str(it.quantity)))
                    self.detail_gui.tableWidget.setItem(current_row, 5, QTableWidgetItem(get_money_format(float(it.price))))
                    self.detail_gui.tableWidget.setItem(current_row, 6,
                                                      QTableWidgetItem(get_money_format(float(int(it.quantity) * int(it.price)))))
                    current_row = current_row + 1
                    sub_total += float(int(it.quantity) * int(it.price))
            else:
                self.detail_gui.tableWidget.setItem(current_row, 0, QTableWidgetItem(str(current_row + 1)))
                self.detail_gui.tableWidget.setItem(current_row, 1, QTableWidgetItem(str(item.sku)))
                self.detail_gui.tableWidget.setItem(current_row, 2, QTableWidgetItem(item.product_name))
                self.detail_gui.tableWidget.setItem(current_row, 3, QTableWidgetItem(item.unit))
                self.detail_gui.tableWidget.setItem(current_row, 4, QTableWidgetItem(str(item.quantity)))
                self.detail_gui.tableWidget.setItem(current_row, 5, QTableWidgetItem(get_money_format(float(item.price))))
                self.detail_gui.tableWidget.setItem(current_row, 6,
                                                  QTableWidgetItem(get_money_format(float(int(item.quantity) * int(item.price)))))
                sub_total += float(int(item.quantity) * int(item.price))
                current_row = current_row + 1

        if sum(float(item.discount_amount) for item in order.order_line_items) > 0:
            self.detail_gui.tableWidget.setItem(current_row, 2,
                                              QTableWidgetItem(f"Khuyến mãi của công ty theo chương trình khuyến mãi "
                                                               f"{created_date.month}/{created_date.year} "
                                                               f"trên sàn {order.source_name}"))
            self.detail_gui.tableWidget.setItem(current_row, 6,
                                                QTableWidgetItem(get_money_format(sum(float(item.discount_amount)
                                                                         for item in order.order_line_items)/1.1)))
            current_row = current_row + 1
            sub_total = sub_total - sum(float(item.discount_amount) for item in order.order_line_items)/1.1

        if sum(float(item.distributed_discount_amount) for item in order.order_line_items) > 0:
            self.detail_gui.tableWidget.setItem(current_row, 2, QTableWidgetItem(
                                            f"Khuyến mãi trên sàn {order.source_name} theo chương trình khuyến mãi "
                                            f"của sàn {created_date.month}/{created_date.year} "))

            self.detail_gui.tableWidget.setItem(current_row, 6,
                                                QTableWidgetItem(get_money_format(sum(float(item.distributed_discount_amount)
                                                                         for item in order.order_line_items)/1.1)))
            current_row = current_row + 1
            sub_total = sub_total - sum(float(item.distributed_discount_amount) for item in order.order_line_items)/1.1

        self.detail_gui.tableWidget.setItem(current_row, 2, QTableWidgetItem(f"Bổ sung đơn hàng ngày "
                                                                             f"{created_date.day}/{created_date.month}/{created_date.year}"
                                                                             f"(Mã đơn hàng: {order.code})"))
        # sub_total
        self.detail_gui.lbSubTotal.setText(get_money_format(float(sub_total)))
