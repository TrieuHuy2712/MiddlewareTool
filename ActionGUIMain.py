from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QTableWidgetItem, QHeaderView, QPushButton, QCheckBox, QWidget, \
    QHBoxLayout
from PyQt5.uic.properties import QtCore

import GUIDetail
from DetailGUIMain import DetailGUIMain
from GUIMain import Ui_MainWindow
from src.Enums import SapoShop, Category, Channel, OrderStatus
from src.Factory.OrderFactory import OrderAutoFactory, OrderAPIFactory, OrderFactory
from src.Model.Order import Order
from src.OrderRequest import OrderRequest
from src.utils import set_default_if_none, get_current_date_time_to_midnight


class QStringLiteral:
    pass


class ActionMainGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_gui = Ui_MainWindow()
        self.main_gui.setupUi(self)
        self.list_items = ["Sapo - Shop thảo dược Giang", "Sapo - Quốc Cơ Quốc Nghiệp", "Web"]
        self.list_orders_items = ["Đang giao hàng", "Đã hoàn thành"]
        self.add_default_value()
        self.add_action()
        self.show()
        self.order_factory = None
        self.detail = DetailGUIMain()
        self.orders = []
        self.checkboxes = []

    def add_action(self):
        self.main_gui.btnSearch.clicked.connect(self.action_click_search)
        self.main_gui.cbSearchType.currentTextChanged.connect(self.changing_search_type)
        self.main_gui.btnSubmit.clicked.connect(self.action_click_submit)

    def add_default_value(self):
        self.main_gui.cbFilter.addItems(self.list_items)
        self.main_gui.cbFilter.setEditable(True)
        self.main_gui.cbFilter.lineEdit().setPlaceholderText("---Vui lòng chọn kênh---")
        self.main_gui.cbSelectOrder.addItems(self.list_orders_items)
        table_headers = ["", "Mã hóa đơn", "Thông tin khách hàng", "Ngày tạo", "Giá", "Nguồn", "Chi tiết"]
        self.main_gui.tableWidget.setColumnCount(len(table_headers))
        self.main_gui.tableWidget.setHorizontalHeaderLabels(table_headers)
        # Table header
        for index, ele in enumerate(table_headers):
            self.main_gui.tableWidget.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)

        filter_order_type = ["Tìm hóa đơn theo ngày tháng", "Tìm kiếm thông thường",
                             "Tìm hóa đơn cụ thể theo ngày tháng"]
        self.main_gui.cbSearchType.addItems(filter_order_type)

        # Set datetime
        self.main_gui.dateTimeTo.setDateTime(get_current_date_time_to_midnight(date_diff=1))
        self.main_gui.dateTimeFrom.setDateTime(get_current_date_time_to_midnight(date_diff=-7))

    def changing_search_type(self):
        if self.main_gui.cbSearchType.currentIndex() == 0:
            # Find order by datetime
            self.main_gui.tbSearch.setReadOnly(True)
            self.main_gui.dateTimeTo.setReadOnly(False)
            self.main_gui.dateTimeFrom.setReadOnly(False)
        elif self.main_gui.cbSearchType.currentIndex() == 1:
            # Find order normally
            self.main_gui.tbSearch.setReadOnly(False)
            self.main_gui.dateTimeTo.setReadOnly(True)
            self.main_gui.dateTimeFrom.setReadOnly(True)
        elif self.main_gui.cbSearchType.currentIndex() == 2:
            # Find order by order search and datetime
            self.main_gui.tbSearch.setReadOnly(False)
            self.main_gui.dateTimeTo.setReadOnly(False)
            self.main_gui.dateTimeFrom.setReadOnly(False)

    def action_click_submit(self):
        if list(filter(lambda o: o.sent_to_misa == True,self.orders)) == 0:
            QMessageBox.critical(self, 'Lỗi', 'Không tìm thầy hóa đơn. Bạn vui lòng nhập tìm lại', QMessageBox.Ok)
        else:
            if self.main_gui.cbFilter.currentIndex() == 2: # Submit at web
                self.order_factory.submit_order(list(filter(lambda o: o.sent_to_misa == True, self.orders)), Channel.WEB)
            else: # Submit at Sapo
                self.order_factory.submit_order(list(filter(lambda o: o.sent_to_misa == True, self.orders)), Channel.SAPO)
            QMessageBox.information(self, 'Thông báo', 'Đã thêm hóa đơn vào Misa!', QMessageBox.Ok)

    def action_click_search(self):
        search_text = self.main_gui.tbSearch.toPlainText()
        if search_text is None or search_text.strip() == "" and (
                self.main_gui.cbSearchType.currentIndex() == 1 or self.main_gui.cbSearchType.currentIndex() == 2):
            QMessageBox.critical(self, 'Lỗi', 'Vui lòng nhập hóa đơn tìm kiếm', QMessageBox.Ok)
        else:
            search_orders = list(set(x.strip() for x in search_text.split(',')))
            if len(search_orders) == 0:
                QMessageBox.critical(self, 'Lỗi', 'Không tìm thấy danh sách hóa đơn', QMessageBox.Ok)
                return

            # Prepare the order request
            order_request = OrderRequest()
            order_request.status = OrderStatus.SHIPPING if self.main_gui.cbSelectOrder.currentIndex() == OrderStatus.SHIPPING.value else OrderStatus.COMPLETE

            # Handle search type and prepare request
            if self.main_gui.cbSearchType.currentIndex() == 0 or self.main_gui.cbSearchType.currentIndex() == 2:
                order_request.from_date = self.main_gui.dateTimeFrom.dateTime().toString("yyyy-MM-ddThh:mm:ssZ")
                order_request.to_date = self.main_gui.dateTimeTo.dateTime().toString("yyyy-MM-ddThh:mm:ssZ")
            if self.main_gui.cbSearchType.currentIndex() == 1 or self.main_gui.cbSearchType.currentIndex() == 2:
                order_request.orders = search_orders

            # Handle filter channel

            if self.main_gui.cbFilter.currentIndex() == 0:  # Sapo Thảo dược Giang
                self.order_factory = OrderFactory.set_category_request(Category.AUTO)
                order_method = self.order_factory.create_sapo_order(order_request, SapoShop.ThaoDuocGiang)
            elif self.main_gui.cbFilter.currentIndex() == 1:  # Sapo Quốc Cơ Quốc Nghiệp
                self.order_factory = OrderFactory.set_category_request(Category.AUTO)
                order_method = self.order_factory.create_sapo_order(order_request, SapoShop.QuocCoQuocNghiepShop)
            elif self.main_gui.cbFilter.currentIndex() == 2:  # Web
                self.order_factory = OrderFactory.set_category_request(Category.API)
                order_method = self.order_factory.create_web_order(order_request)
            else:
                QMessageBox.critical(self, 'Lỗi', 'Vui lòng chọn kênh', QMessageBox.Ok)
                return

            # Handle search type and prepare request
            if self.main_gui.cbSearchType.currentIndex() == 0:
                orders = order_method.get_orders_by_date()
            elif self.main_gui.cbSearchType.currentIndex() == 1:
                orders = order_method.get_orders_by_search()
            else:
                orders = order_method.get_orders_by_search_and_date()

            self.main_gui.cbSelectAll.stateChanged.connect(
                lambda state: self.change_state_all_orders_sent_to_misa(state))
            self.main_gui.tableWidget.setRowCount(len(orders))
            self.orders = orders
            self.create_detail_table()
            QMessageBox.information(self, 'Thông báo', 'Đã lấy hóa đơn từ Sapo theo bộ lọc', QMessageBox.Ok)

    def go_to_detail_page(self, order: Order):
        self.detail.get_order_detail(order)
        self.detail.show()

    def set_check_all_state(self):
        # Check all orders is request to Misa
        if len([order for order in self.orders if order.sent_to_misa is True]) == len(self.orders):
            # 0 un-checked
            # 2 checked state
            self.main_gui.cbSelectAll.setChecked(True)
        # else:
        #     self.main_gui.cbSelectAll.setCheckState(1)

    def change_state_sent_to_misa(self, state, order: Order):
        for ord in self.orders:
            if ord.code == order.code:
                ord.sent_to_misa = not ord.sent_to_misa
                break
        self.set_check_all_state()

    def change_state_all_orders_sent_to_misa(self, state):
        # 0 un-checked
        # 2 checked state
        for order in self.orders:
            if state == 0:
                order.sent_to_misa = False
            elif state == 2:
                order.sent_to_misa = True
        self.create_detail_table()

    def create_detail_table(self):
        current_row = 0
        for order in self.orders:
            # Checkbox
            checkbox = QCheckBox(self.main_gui.tableWidget)
            checkbox.setObjectName(f"cbx_{str(order.code)}")
            checkbox.setChecked(order.sent_to_misa)
            if checkbox.isChecked():
                order.sent_to_misa = True
            else:
                order.sent_to_misa = False

            checkbox.stateChanged.connect(lambda state, order=order: self.change_state_sent_to_misa(state, order))
            self.checkboxes.append(checkbox)
            cell_widget = QWidget()
            lay_out = QHBoxLayout(cell_widget)
            lay_out.addWidget(checkbox)
            lay_out.setAlignment(Qt.AlignCenter)
            lay_out.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(lay_out)

            self.main_gui.tableWidget.setCellWidget(current_row, 0, cell_widget)
            self.main_gui.tableWidget.setItem(current_row, 1, QTableWidgetItem(order.code))
            self.main_gui.tableWidget.setItem(current_row, 2,
                                              QTableWidgetItem(f"{set_default_if_none(order.customer_data.name)}"
                                                               f" - {set_default_if_none(order.customer_data.phone_number)}"))
            self.main_gui.tableWidget.setItem(current_row, 3, QTableWidgetItem(order.created_on))
            self.main_gui.tableWidget.setItem(current_row, 4, QTableWidgetItem(str(order.total)))
            self.main_gui.tableWidget.setItem(current_row, 5, QTableWidgetItem(str(order.source_name)))
            btn = QPushButton(self.main_gui.tableWidget)
            btn.setText('Xem')
            btn.setObjectName(str(order.code))

            self.main_gui.tableWidget.setCellWidget(current_row, 6, btn)

            btn.clicked.connect(lambda checked, order=order: self.go_to_detail_page(order))
            current_row = current_row + 1

        self.set_check_all_state()
