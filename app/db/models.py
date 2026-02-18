from typing import Optional, List
import datetime
import decimal

from sqlalchemy import CHAR, Column, DateTime, Index, Integer, LargeBinary, NCHAR, PrimaryKeyConstraint, TIMESTAMP, \
    Table, VARCHAR, text, ForeignKey
from sqlalchemy.dialects.oracle import NUMBER
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ApprovedRefund(Base):
    __tablename__ = "approved_refunds"
    __table_args__ = {"schema": "DASORP_TEST"}

    # Primary key
    sior_id: Mapped[float] = mapped_column(NUMBER(11, 0, False), primary_key=True)

    # Остальные колонки таблицы approved_refunds
    mhmh_id: Mapped[float] = mapped_column(NUMBER(11, 0, False), nullable=False)
    status: Mapped[int] = mapped_column(NUMBER(3, 0, False), nullable=False)
    recv_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    doc_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    knp: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    code1c: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    refer_in: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    letter_num: Mapped[Optional[str]] = mapped_column(VARCHAR(20))
    sum_all: Mapped[Optional[decimal.Decimal]] = mapped_column(NUMBER(16, 2, True))
    cnt_rows: Mapped[int] = mapped_column(NUMBER(5, 0, False), nullable=False)
    message_id: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    c1_state: Mapped[int] = mapped_column(NUMBER(3, 0, False), nullable=False)
    c1_doc_number: Mapped[Optional[str]] = mapped_column(VARCHAR(32))
    c1_doc_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    swift_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    type_payer: Mapped[Optional[str]] = mapped_column(VARCHAR(4))

    # Relationship к деталям
    items: Mapped[List["ApprovedRefundItem"]] = relationship(
        "ApprovedRefundItem",
        back_populates="refund"
    )


class ApprovedRefundItem(Base):
    __tablename__ = "approved_refunds_list"
    __table_args__ = {"schema": "DASORP_TEST"}

    # Primary key
    ret_num: Mapped[float] = mapped_column(NUMBER(12, 0, False), primary_key=True)

    # Foreign key
    sior_id: Mapped[float] = mapped_column(
        NUMBER(11, 0, False),
        ForeignKey("DASORP_TEST.approved_refunds.sior_id"),
        nullable=False
    )

    # Остальные колонки таблицы approved_refunds_list
    mhmh_id: Mapped[float] = mapped_column(NUMBER(11, 0, False), nullable=False)
    recv_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    doc_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    iin: Mapped[str] = mapped_column(VARCHAR(13), nullable=False)
    pmdl_n: Mapped[float] = mapped_column(NUMBER(asdecimal=False), nullable=False)
    line_refund: Mapped[float] = mapped_column(NUMBER(asdecimal=False), nullable=False)
    sum_gfss: Mapped[Optional[decimal.Decimal]] = mapped_column(NUMBER(19, 2, True))
    refer_gfss: Mapped[Optional[str]] = mapped_column(VARCHAR(32))

    # Relationship к header
    refund: Mapped["ApprovedRefund"] = relationship(
        "ApprovedRefund",
        back_populates="items"
    )


class Service1cExchange(Base):
    __tablename__ = 'service_1c_exchange'
    __table_args__ = (
        Index('xn_service_1c_exchange_mhmh', 'mhmh_id'),
        {'schema': 'DASORP_TEST'}
    )

    # Primary key
    id: Mapped[float] = mapped_column(NUMBER(10, 0, False), primary_key=True)

    # Колонки header
    mhmh_id: Mapped[Optional[float]] = mapped_column(NUMBER(10, 0, False))
    date_op: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    state: Mapped[Optional[float]] = mapped_column(NUMBER(10, 0, False))
    knp: Mapped[Optional[str]] = mapped_column(CHAR(3))
    code1c: Mapped[Optional[str]] = mapped_column(VARCHAR(16))
    date_creation: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    pay_sum: Mapped[Optional[decimal.Decimal]] = mapped_column(NUMBER(16, 2, True))
    send: Mapped[Optional[str]] = mapped_column(VARCHAR(5))
    vo: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    pso: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    currency: Mapped[Optional[str]] = mapped_column(VARCHAR(5))
    assign: Mapped[Optional[str]] = mapped_column(VARCHAR(2000))
    prt: Mapped[Optional[str]] = mapped_column(VARCHAR(5))
    pay_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    doc_nmb: Mapped[Optional[str]] = mapped_column(VARCHAR(32))
    doc_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    refer: Mapped[Optional[str]] = mapped_column(VARCHAR(32))

    # Relationship к деталям
    items: Mapped[List["Service1cExchangeItem"]] = relationship(
        "Service1cExchangeItem",
        back_populates="exchange",
        cascade="all, delete-orphan",
        primaryjoin="Service1cExchange.id==Service1cExchangeItem.file_id"
    )


class Service1cExchangeItem(Base):
    __tablename__ = 'service_1c_exchange_list'
    __table_args__ = (
        Index('xn_serv_1c_doc_nmb', 'doc_nmb', 'doc_date'),
        Index('xn_service_1c_list_file_id', 'file_id'),
        Index('xn_service_1c_list_retnum', 'ret_num', unique=True),
        {'schema': 'DASORP_TEST'}
    )

    # Primary key
    ret_num: Mapped[float] = mapped_column(NUMBER(10, 0, False), primary_key=True)

    # Foreign key (можно закомментировать, если физически нет FK)
    file_id: Mapped[Optional[float]] = mapped_column(
        NUMBER(10, 0, False),
        ForeignKey("DASORP_TEST.service_1c_exchange.id", ondelete="CASCADE"),
        nullable=True
    )

    pmdl_n: Mapped[Optional[float]] = mapped_column(NUMBER(10, 0, False))
    sior_id: Mapped[Optional[float]] = mapped_column(NUMBER(10, 0, False))
    sum_gfss: Mapped[Optional[decimal.Decimal]] = mapped_column(NUMBER(16, 2, True))
    period: Mapped[Optional[str]] = mapped_column(VARCHAR(6))
    pay_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    doc_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    doc_nmb: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    lastname: Mapped[Optional[str]] = mapped_column(VARCHAR(200))
    firstname: Mapped[Optional[str]] = mapped_column(VARCHAR(200))
    middlename: Mapped[Optional[str]] = mapped_column(VARCHAR(200))
    dt: Mapped[Optional[str]] = mapped_column(VARCHAR(32))
    iin: Mapped[Optional[str]] = mapped_column(VARCHAR(12))
    assign: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    refer: Mapped[Optional[str]] = mapped_column(VARCHAR(200))

    # Relationship к header
    exchange: Mapped["Service1cExchange"] = relationship(
        "Service1cExchange",
        back_populates="items"
    )


class Person(Base):
    __tablename__ = 'person'
    __table_args__ = (
        Index('xn0_person_iin', 'iin', unique=True),
        Index('xn1_person_sicid', 'sicid', unique=True),
        Index('xn2_fio_person', 'lastname', 'firstname', 'middlename'),
        {'schema': 'LOADER'}
    )

    # Предположительно primary key — sicid (уникальный индекс).
    sicid: Mapped[int] = mapped_column(NUMBER(11, 0, False), primary_key=True)

    iin: Mapped[Optional[str]] = mapped_column(VARCHAR(12))
    actid: Mapped[Optional[int]] = mapped_column(NUMBER(11, 0, False))
    citizenship_id: Mapped[Optional[int]] = mapped_column(NUMBER(asdecimal=False))

    lastname: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    firstname: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    middlename: Mapped[Optional[str]] = mapped_column(VARCHAR(60))

    birthdate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    birthplace: Mapped[Optional[str]] = mapped_column(VARCHAR(140))

    sic: Mapped[Optional[str]] = mapped_column(VARCHAR(32))

    doctype: Mapped[Optional[str]] = mapped_column(VARCHAR(4))
    docdate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    docser: Mapped[Optional[str]] = mapped_column(VARCHAR(20))
    docnum: Mapped[Optional[str]] = mapped_column(VARCHAR(30))
    docplace: Mapped[Optional[str]] = mapped_column(VARCHAR(140))

    resident: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    address: Mapped[Optional[str]] = mapped_column(VARCHAR(300))
    homephone: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    # sex: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    #
    # rlastname: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    # rfirstname: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    # rmiddlename: Mapped[Optional[str]] = mapped_column(VARCHAR(60))
    #
    # branchid: Mapped[Optional[str]] = mapped_column(CHAR(4))
    # actdate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    # filldate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    #
    # statusgen: Mapped[Optional[int]] = mapped_column(NUMBER(2, 0, False))
    # status: Mapped[Optional[int]] = mapped_column(NUMBER(1, 0, False))
    # stgenold: Mapped[Optional[int]] = mapped_column(NUMBER(1, 0, False))
    #
    # regdate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    # regdate_old: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    #
    # category: Mapped[Optional[int]] = mapped_column(NUMBER(3, 0, False))
    # rnn: Mapped[Optional[str]] = mapped_column(VARCHAR(24))
    #
    # workplace: Mapped[Optional[str]] = mapped_column(VARCHAR(160))
    # workphone: Mapped[Optional[str]] = mapped_column(VARCHAR(16))
    #
    # area: Mapped[Optional[int]] = mapped_column(NUMBER(1, 0, False))
    # empid: Mapped[Optional[int]] = mapped_column(NUMBER(10, 0, False))
    # ordnum: Mapped[Optional[int]] = mapped_column(NUMBER(5, 0, False))
    #
    # rbranchid: Mapped[Optional[str]] = mapped_column(CHAR(4))
    #
    # siap_id: Mapped[Optional[int]] = mapped_column(NUMBER(11, 0, False))
    # correct_id: Mapped[Optional[int]] = mapped_column(NUMBER(11, 0, False))
    #
    # status_mj: Mapped[Optional[int]] = mapped_column(NUMBER(asdecimal=False))