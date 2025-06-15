from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, DECIMAL, Date, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, Table, Unicode, Uuid, text
from sqlalchemy.dialects.mssql import DATETIME2, DATETIMEOFFSET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal
import uuid

class Base(DeclarativeBase):
    pass


class AspNetRoles(Base):
    __tablename__ = 'AspNetRoles'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_AspNetRoles'),
        Index('RoleNameIndex', 'NormalizedName', unique=True)
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[Optional[str]] = mapped_column(Unicode(256, 'SQL_Latin1_General_CP1_CI_AS'))
    NormalizedName: Mapped[Optional[str]] = mapped_column(Unicode(256, 'SQL_Latin1_General_CP1_CI_AS'))
    ConcurrencyStamp: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    AspNetUsers: Mapped[List['AspNetUsers']] = relationship('AspNetUsers', secondary='AspNetUserRoles', back_populates='AspNetRoles_')
    AspNetRoleClaims: Mapped[List['AspNetRoleClaims']] = relationship('AspNetRoleClaims', back_populates='AspNetRoles_')


class AspNetUsers(Base):
    __tablename__ = 'AspNetUsers'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_AspNetUsers'),
        Index('EmailIndex', 'NormalizedEmail'),
        Index('UserNameIndex', 'NormalizedUserName', unique=True)
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(100, 'SQL_Latin1_General_CP1_CI_AS'))
    IsActive: Mapped[bool] = mapped_column(Boolean, server_default=text('(CONVERT([bit],(1)))'))
    CustomerPoints: Mapped[int] = mapped_column(Integer, server_default=text('((0))'))
    CustomerLevel: Mapped[int] = mapped_column(Integer, server_default=text('((0))'))
    UserName: Mapped[str] = mapped_column(Unicode(50, 'SQL_Latin1_General_CP1_CI_AS'))
    Email: Mapped[str] = mapped_column(Unicode(100, 'SQL_Latin1_General_CP1_CI_AS'))
    EmailConfirmed: Mapped[bool] = mapped_column(Boolean)
    PasswordHash: Mapped[str] = mapped_column(Unicode(100, 'SQL_Latin1_General_CP1_CI_AS'))
    PhoneNumber: Mapped[str] = mapped_column(Unicode(15, 'SQL_Latin1_General_CP1_CI_AS'))
    PhoneNumberConfirmed: Mapped[bool] = mapped_column(Boolean)
    TwoFactorEnabled: Mapped[bool] = mapped_column(Boolean)
    LockoutEnabled: Mapped[bool] = mapped_column(Boolean)
    AccessFailedCount: Mapped[int] = mapped_column(Integer)
    ImageUrl: Mapped[Optional[str]] = mapped_column(Unicode(200, 'SQL_Latin1_General_CP1_CI_AS'))
    DateOfBirth: Mapped[Optional[datetime.date]] = mapped_column(Date)
    NormalizedUserName: Mapped[Optional[str]] = mapped_column(Unicode(256, 'SQL_Latin1_General_CP1_CI_AS'))
    NormalizedEmail: Mapped[Optional[str]] = mapped_column(Unicode(256, 'SQL_Latin1_General_CP1_CI_AS'))
    SecurityStamp: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ConcurrencyStamp: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    LockoutEnd: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIMEOFFSET)

    AspNetRoles_: Mapped[List['AspNetRoles']] = relationship('AspNetRoles', secondary='AspNetUserRoles', back_populates='AspNetUsers')
    Addresses: Mapped[List['Addresses']] = relationship('Addresses', back_populates='AspNetUsers_')
    AspNetUserClaims: Mapped[List['AspNetUserClaims']] = relationship('AspNetUserClaims', back_populates='AspNetUsers_')
    AspNetUserLogins: Mapped[List['AspNetUserLogins']] = relationship('AspNetUserLogins', back_populates='AspNetUsers_')
    AspNetUserTokens: Mapped[List['AspNetUserTokens']] = relationship('AspNetUserTokens', back_populates='AspNetUsers_')
    Payments: Mapped[List['Payments']] = relationship('Payments', back_populates='AspNetUsers_')
    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='AspNetUsers_')
    Reviews: Mapped[List['Reviews']] = relationship('Reviews', back_populates='AspNetUsers_')


class Attributes(Base):
    __tablename__ = 'Attributes'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_Attributes'),
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Type: Mapped[int] = mapped_column(Integer)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    CategoryAttributes: Mapped[List['CategoryAttributes']] = relationship('CategoryAttributes', back_populates='Attributes_')
    AttributeValues: Mapped[List['AttributeValues']] = relationship('AttributeValues', back_populates='Attributes_')


class Categories(Base):
    __tablename__ = 'Categories'
    __table_args__ = (
        ForeignKeyConstraint(['ParentCategoryId'], ['Categories.Id'], name='FK_Categories_Categories_ParentCategoryId'),
        PrimaryKeyConstraint('Id', name='PK_Categories'),
        Index('IX_Categories_ParentCategoryId', 'ParentCategoryId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(100, 'SQL_Latin1_General_CP1_CI_AS'))
    Slug: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    Description: Mapped[Optional[str]] = mapped_column(Unicode(500, 'SQL_Latin1_General_CP1_CI_AS'))
    ImageUrl: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ParentCategoryId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    Categories: Mapped[Optional['Categories']] = relationship('Categories', remote_side=[Id], back_populates='Categories_reverse')
    Categories_reverse: Mapped[List['Categories']] = relationship('Categories', remote_side=[ParentCategoryId], back_populates='Categories')
    CategoryAttributes: Mapped[List['CategoryAttributes']] = relationship('CategoryAttributes', back_populates='Categories_')
    Products: Mapped[List['Products']] = relationship('Products', back_populates='Categories_')


class Combos(Base):
    __tablename__ = 'Combos'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_Combos'),
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Description: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    DiscountPercentage: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    IsActive: Mapped[bool] = mapped_column(Boolean)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    ProductCombos: Mapped[List['ProductCombos']] = relationship('ProductCombos', back_populates='Combos_')


class Placements(Base):
    __tablename__ = 'Placements'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_Placements'),
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    Description: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    Products: Mapped[List['Products']] = relationship('Products', back_populates='Placements_')


class Promotions(Base):
    __tablename__ = 'Promotions'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_Promotions'),
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Code: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    DiscountPercentage: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    StartDate: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    EndDate: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    IsActive: Mapped[bool] = mapped_column(Boolean)
    Ussage: Mapped[int] = mapped_column(Integer)
    CustomerLevel: Mapped[int] = mapped_column(Integer)
    Type: Mapped[int] = mapped_column(Integer)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    Description: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ProductIds: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    Products: Mapped[List['Products']] = relationship('Products', secondary='ProductPromotion', back_populates='Promotions_')
    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='Promotions_')


class VerificationCodes(Base):
    __tablename__ = 'VerificationCodes'
    __table_args__ = (
        PrimaryKeyConstraint('Id', name='PK_VerificationCodes'),
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Code: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Email: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ExpirationDate: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)


class EFMigrationsHistory(Base):
    __tablename__ = '__EFMigrationsHistory'
    __table_args__ = (
        PrimaryKeyConstraint('MigrationId', name='PK___EFMigrationsHistory'),
    )

    MigrationId: Mapped[str] = mapped_column(Unicode(150, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    ProductVersion: Mapped[str] = mapped_column(Unicode(32, 'SQL_Latin1_General_CP1_CI_AS'))


class Addresses(Base):
    __tablename__ = 'Addresses'
    __table_args__ = (
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], ondelete='CASCADE', name='FK_Addresses_AspNetUsers_UserId'),
        PrimaryKeyConstraint('Id', name='PK_Addresses'),
        Index('IX_Addresses_UserId', 'UserId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    IsDefault: Mapped[bool] = mapped_column(Boolean)
    UserId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    Street: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    District: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    City: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    PostalCode: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Country: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Ward: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    AspNetUsers_: Mapped['AspNetUsers'] = relationship('AspNetUsers', back_populates='Addresses')
    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='Addresses_')


class AspNetRoleClaims(Base):
    __tablename__ = 'AspNetRoleClaims'
    __table_args__ = (
        ForeignKeyConstraint(['RoleId'], ['AspNetRoles.Id'], ondelete='CASCADE', name='FK_AspNetRoleClaims_AspNetRoles_RoleId'),
        PrimaryKeyConstraint('Id', name='PK_AspNetRoleClaims'),
        Index('IX_AspNetRoleClaims_RoleId', 'RoleId')
    )

    Id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    RoleId: Mapped[uuid.UUID] = mapped_column(Uuid)
    ClaimType: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ClaimValue: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    AspNetRoles_: Mapped['AspNetRoles'] = relationship('AspNetRoles', back_populates='AspNetRoleClaims')


class AspNetUserClaims(Base):
    __tablename__ = 'AspNetUserClaims'
    __table_args__ = (
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], ondelete='CASCADE', name='FK_AspNetUserClaims_AspNetUsers_UserId'),
        PrimaryKeyConstraint('Id', name='PK_AspNetUserClaims'),
        Index('IX_AspNetUserClaims_UserId', 'UserId')
    )

    Id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    UserId: Mapped[uuid.UUID] = mapped_column(Uuid)
    ClaimType: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ClaimValue: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    AspNetUsers_: Mapped['AspNetUsers'] = relationship('AspNetUsers', back_populates='AspNetUserClaims')


class AspNetUserLogins(Base):
    __tablename__ = 'AspNetUserLogins'
    __table_args__ = (
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], ondelete='CASCADE', name='FK_AspNetUserLogins_AspNetUsers_UserId'),
        PrimaryKeyConstraint('LoginProvider', 'ProviderKey', name='PK_AspNetUserLogins'),
        Index('IX_AspNetUserLogins_UserId', 'UserId')
    )

    LoginProvider: Mapped[str] = mapped_column(Unicode(450, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    ProviderKey: Mapped[str] = mapped_column(Unicode(450, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    UserId: Mapped[uuid.UUID] = mapped_column(Uuid)
    ProviderDisplayName: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    AspNetUsers_: Mapped['AspNetUsers'] = relationship('AspNetUsers', back_populates='AspNetUserLogins')


t_AspNetUserRoles = Table(
    'AspNetUserRoles', Base.metadata,
    Column('UserId', Uuid, primary_key=True, nullable=False),
    Column('RoleId', Uuid, primary_key=True, nullable=False),
    ForeignKeyConstraint(['RoleId'], ['AspNetRoles.Id'], ondelete='CASCADE', name='FK_AspNetUserRoles_AspNetRoles_RoleId'),
    ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], ondelete='CASCADE', name='FK_AspNetUserRoles_AspNetUsers_UserId'),
    PrimaryKeyConstraint('UserId', 'RoleId', name='PK_AspNetUserRoles'),
    Index('IX_AspNetUserRoles_RoleId', 'RoleId')
)


class AspNetUserTokens(Base):
    __tablename__ = 'AspNetUserTokens'
    __table_args__ = (
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], ondelete='CASCADE', name='FK_AspNetUserTokens_AspNetUsers_UserId'),
        PrimaryKeyConstraint('UserId', 'LoginProvider', 'Name', name='PK_AspNetUserTokens')
    )

    UserId: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    LoginProvider: Mapped[str] = mapped_column(Unicode(450, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(450, 'SQL_Latin1_General_CP1_CI_AS'), primary_key=True)
    Value: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    AspNetUsers_: Mapped['AspNetUsers'] = relationship('AspNetUsers', back_populates='AspNetUserTokens')


class CategoryAttributes(Base):
    __tablename__ = 'CategoryAttributes'
    __table_args__ = (
        ForeignKeyConstraint(['AttributeId'], ['Attributes.Id'], ondelete='CASCADE', name='FK_CategoryAttributes_Attributes_AttributeId'),
        ForeignKeyConstraint(['CategoryId'], ['Categories.Id'], ondelete='CASCADE', name='FK_CategoryAttributes_Categories_CategoryId'),
        PrimaryKeyConstraint('Id', name='PK_CategoryAttributes'),
        Index('IX_CategoryAttributes_AttributeId', 'AttributeId'),
        Index('IX_CategoryAttributes_CategoryId', 'CategoryId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    CategoryId: Mapped[uuid.UUID] = mapped_column(Uuid)
    AttributeId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    Attributes_: Mapped['Attributes'] = relationship('Attributes', back_populates='CategoryAttributes')
    Categories_: Mapped['Categories'] = relationship('Categories', back_populates='CategoryAttributes')


class Payments(Base):
    __tablename__ = 'Payments'
    __table_args__ = (
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], ondelete='CASCADE', name='FK_Payments_AspNetUsers_UserId'),
        PrimaryKeyConstraint('Id', name='PK_Payments'),
        Index('IX_Payments_UserId', 'UserId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    CardHolderName: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    CardNumber: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    CardType: Mapped[str] = mapped_column(Unicode(20, 'SQL_Latin1_General_CP1_CI_AS'))
    ExpirationDate: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Method: Mapped[str] = mapped_column(Unicode(20, 'SQL_Latin1_General_CP1_CI_AS'))
    IsDefault: Mapped[bool] = mapped_column(Boolean, server_default=text('(CONVERT([bit],(0)))'))
    UserId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    AspNetUsers_: Mapped['AspNetUsers'] = relationship('AspNetUsers', back_populates='Payments')
    Orders: Mapped[List['Orders']] = relationship('Orders', back_populates='Payments_')


class Products(Base):
    __tablename__ = 'Products'
    __table_args__ = (
        ForeignKeyConstraint(['CategoryId'], ['Categories.Id'], ondelete='CASCADE', name='FK_Products_Categories_CategoryId'),
        ForeignKeyConstraint(['PlacementId'], ['Placements.Id'], ondelete='CASCADE', name='FK_Products_Placements_PlacementId'),
        PrimaryKeyConstraint('Id', name='PK_Products'),
        Index('IX_Products_CategoryId', 'CategoryId'),
        Index('IX_Products_PlacementId', 'PlacementId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Name: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    Price: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    Description: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    IsActive: Mapped[bool] = mapped_column(Boolean)
    CategoryId: Mapped[uuid.UUID] = mapped_column(Uuid)
    PlacementId: Mapped[uuid.UUID] = mapped_column(Uuid)
    Status: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    ImageUrl: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ModelUrl: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))

    Categories_: Mapped['Categories'] = relationship('Categories', back_populates='Products')
    Placements_: Mapped['Placements'] = relationship('Placements', back_populates='Products')
    Promotions_: Mapped[List['Promotions']] = relationship('Promotions', secondary='ProductPromotion', back_populates='Products')
    AttributeValues: Mapped[List['AttributeValues']] = relationship('AttributeValues', back_populates='Products_')
    ProductCombos: Mapped[List['ProductCombos']] = relationship('ProductCombos', back_populates='Products_')
    Variants: Mapped[List['Variants']] = relationship('Variants', back_populates='Products_')


class AttributeValues(Base):
    __tablename__ = 'AttributeValues'
    __table_args__ = (
        ForeignKeyConstraint(['AttributeId'], ['Attributes.Id'], ondelete='CASCADE', name='FK_AttributeValues_Attributes_AttributeId'),
        ForeignKeyConstraint(['ProductId'], ['Products.Id'], name='FK_AttributeValues_Products_ProductId'),
        PrimaryKeyConstraint('Id', name='PK_AttributeValues'),
        Index('IX_AttributeValues_AttributeId', 'AttributeId'),
        Index('IX_AttributeValues_ProductId', 'ProductId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Value: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    AttributeId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    ProductId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    Attributes_: Mapped['Attributes'] = relationship('Attributes', back_populates='AttributeValues')
    Products_: Mapped[Optional['Products']] = relationship('Products', back_populates='AttributeValues')
    VariantAttributes: Mapped[List['VariantAttributes']] = relationship('VariantAttributes', back_populates='AttributeValues_')


class Orders(Base):
    __tablename__ = 'Orders'
    __table_args__ = (
        ForeignKeyConstraint(['AddressId'], ['Addresses.Id'], name='FK_Orders_Addresses_AddressId'),
        ForeignKeyConstraint(['PaymentId'], ['Payments.Id'], name='FK_Orders_Payments_PaymentId'),
        ForeignKeyConstraint(['PromotionId'], ['Promotions.Id'], name='FK_Orders_Promotions_PromotionId'),
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], name='FK_Orders_AspNetUsers_UserId'),
        PrimaryKeyConstraint('Id', name='PK_Orders'),
        Index('IX_Orders_AddressId', 'AddressId'),
        Index('IX_Orders_PaymentId', 'PaymentId'),
        Index('IX_Orders_PromotionId', 'PromotionId'),
        Index('IX_Orders_UserId', 'UserId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    UserId: Mapped[uuid.UUID] = mapped_column(Uuid)
    AddressId: Mapped[uuid.UUID] = mapped_column(Uuid)
    Status: Mapped[int] = mapped_column(Integer)
    TotalPrice: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    Discount: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    FinalPrice: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    OrderDate: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    PaymentMethod: Mapped[int] = mapped_column(Integer)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    PromotionId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    Note: Mapped[Optional[str]] = mapped_column(Unicode(500, 'SQL_Latin1_General_CP1_CI_AS'))
    PaymentId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    ShippingCode: Mapped[Optional[str]] = mapped_column(Unicode(50, 'SQL_Latin1_General_CP1_CI_AS'))
    ShippingRate: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    PaymentLinkId: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    PaymentLinkUrl: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    PaymentOrderCode: Mapped[Optional[int]] = mapped_column(BigInteger)

    Addresses_: Mapped['Addresses'] = relationship('Addresses', back_populates='Orders')
    Payments_: Mapped[Optional['Payments']] = relationship('Payments', back_populates='Orders')
    Promotions_: Mapped[Optional['Promotions']] = relationship('Promotions', back_populates='Orders')
    AspNetUsers_: Mapped['AspNetUsers'] = relationship('AspNetUsers', back_populates='Orders')
    OrderDetails: Mapped[List['OrderDetails']] = relationship('OrderDetails', back_populates='Orders_')


class ProductCombos(Base):
    __tablename__ = 'ProductCombos'
    __table_args__ = (
        ForeignKeyConstraint(['ComboId'], ['Combos.Id'], ondelete='CASCADE', name='FK_ProductCombos_Combos_ComboId'),
        ForeignKeyConstraint(['ProductId'], ['Products.Id'], ondelete='CASCADE', name='FK_ProductCombos_Products_ProductId'),
        PrimaryKeyConstraint('Id', name='PK_ProductCombos'),
        Index('IX_ProductCombos_ComboId', 'ComboId'),
        Index('IX_ProductCombos_ProductId', 'ProductId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    ProductId: Mapped[uuid.UUID] = mapped_column(Uuid)
    ComboId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    Combos_: Mapped['Combos'] = relationship('Combos', back_populates='ProductCombos')
    Products_: Mapped['Products'] = relationship('Products', back_populates='ProductCombos')


t_ProductPromotion = Table(
    'ProductPromotion', Base.metadata,
    Column('ProductsId', Uuid, primary_key=True, nullable=False),
    Column('PromotionsId', Uuid, primary_key=True, nullable=False),
    ForeignKeyConstraint(['ProductsId'], ['Products.Id'], ondelete='CASCADE', name='FK_ProductPromotion_Products_ProductsId'),
    ForeignKeyConstraint(['PromotionsId'], ['Promotions.Id'], ondelete='CASCADE', name='FK_ProductPromotion_Promotions_PromotionsId'),
    PrimaryKeyConstraint('ProductsId', 'PromotionsId', name='PK_ProductPromotion'),
    Index('IX_ProductPromotion_PromotionsId', 'PromotionsId')
)


class Variants(Base):
    __tablename__ = 'Variants'
    __table_args__ = (
        ForeignKeyConstraint(['ProductId'], ['Products.Id'], name='FK_Variants_Products_ProductId'),
        PrimaryKeyConstraint('Id', name='PK_Variants'),
        Index('IX_Variants_ProductId', 'ProductId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    ImageUrls: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    PriceAdjustment: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    Stock: Mapped[int] = mapped_column(Integer)
    IsActive: Mapped[bool] = mapped_column(Boolean)
    Sku: Mapped[str] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    ProductId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    Products_: Mapped['Products'] = relationship('Products', back_populates='Variants')
    GoodReceivedNotes: Mapped[List['GoodReceivedNotes']] = relationship('GoodReceivedNotes', back_populates='Variants_')
    OrderDetails: Mapped[List['OrderDetails']] = relationship('OrderDetails', back_populates='Variants_')
    VariantAttributes: Mapped[List['VariantAttributes']] = relationship('VariantAttributes', back_populates='Variants_')
    GoodReceivedItems: Mapped[List['GoodReceivedItems']] = relationship('GoodReceivedItems', back_populates='Variants_')


class GoodReceivedNotes(Base):
    __tablename__ = 'GoodReceivedNotes'
    __table_args__ = (
        ForeignKeyConstraint(['VariantId'], ['Variants.Id'], name='FK_GoodReceivedNotes_Variants_VariantId'),
        PrimaryKeyConstraint('Id', name='PK_GoodReceivedNotes'),
        Index('IX_GoodReceivedNotes_VariantId', 'VariantId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    ReceivedDate: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    Quantity: Mapped[int] = mapped_column(Integer)
    TotalCost: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    ShippingCost: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    Status: Mapped[int] = mapped_column(Integer)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    Note: Mapped[Optional[str]] = mapped_column(Unicode(collation='SQL_Latin1_General_CP1_CI_AS'))
    VariantId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    Variants_: Mapped[Optional['Variants']] = relationship('Variants', back_populates='GoodReceivedNotes')
    GoodReceivedItems: Mapped[List['GoodReceivedItems']] = relationship('GoodReceivedItems', back_populates='GoodReceivedNotes_')


class OrderDetails(Base):
    __tablename__ = 'OrderDetails'
    __table_args__ = (
        ForeignKeyConstraint(['OrderId'], ['Orders.Id'], name='FK_OrderDetails_Orders_OrderId'),
        ForeignKeyConstraint(['VariantId'], ['Variants.Id'], name='FK_OrderDetails_Variants_VariantId'),
        PrimaryKeyConstraint('Id', name='PK_OrderDetails'),
        Index('IX_OrderDetails_OrderId', 'OrderId'),
        Index('IX_OrderDetails_VariantId', 'VariantId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    OrderId: Mapped[uuid.UUID] = mapped_column(Uuid)
    VariantId: Mapped[uuid.UUID] = mapped_column(Uuid)
    Quantity: Mapped[int] = mapped_column(Integer, server_default=text('((1))'))
    UnitPrice: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2), server_default=text('((0.0))'))
    TotalPrice: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2), server_default=text('((0.0))'))
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    Orders_: Mapped['Orders'] = relationship('Orders', back_populates='OrderDetails')
    Variants_: Mapped['Variants'] = relationship('Variants', back_populates='OrderDetails')
    Reviews: Mapped[List['Reviews']] = relationship('Reviews', back_populates='OrderDetails_')


class VariantAttributes(Base):
    __tablename__ = 'VariantAttributes'
    __table_args__ = (
        ForeignKeyConstraint(['AttributeValueId'], ['AttributeValues.Id'], name='FK_VariantAttributes_AttributeValues_AttributeValueId'),
        ForeignKeyConstraint(['VariantId'], ['Variants.Id'], ondelete='CASCADE', name='FK_VariantAttributes_Variants_VariantId'),
        PrimaryKeyConstraint('Id', name='PK_VariantAttributes'),
        Index('IX_VariantAttributes_AttributeValueId', 'AttributeValueId'),
        Index('IX_VariantAttributes_VariantId', 'VariantId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    VariantId: Mapped[uuid.UUID] = mapped_column(Uuid)
    AttributeValueId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    AttributeValues_: Mapped['AttributeValues'] = relationship('AttributeValues', back_populates='VariantAttributes')
    Variants_: Mapped['Variants'] = relationship('Variants', back_populates='VariantAttributes')


class GoodReceivedItems(Base):
    __tablename__ = 'GoodReceivedItems'
    __table_args__ = (
        ForeignKeyConstraint(['GoodReceivedNoteId'], ['GoodReceivedNotes.Id'], ondelete='CASCADE', name='FK_GoodReceivedItems_GoodReceivedNotes_GoodReceivedNoteId'),
        ForeignKeyConstraint(['VariantId'], ['Variants.Id'], ondelete='CASCADE', name='FK_GoodReceivedItems_Variants_VariantId'),
        PrimaryKeyConstraint('Id', name='PK_GoodReceivedItems'),
        Index('IX_GoodReceivedItems_GoodReceivedNoteId', 'GoodReceivedNoteId'),
        Index('IX_GoodReceivedItems_VariantId', 'VariantId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    VariantId: Mapped[uuid.UUID] = mapped_column(Uuid)
    GoodReceivedNoteId: Mapped[uuid.UUID] = mapped_column(Uuid)
    Quantity: Mapped[int] = mapped_column(Integer)
    UnitCost: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    TotalCost: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)

    GoodReceivedNotes_: Mapped['GoodReceivedNotes'] = relationship('GoodReceivedNotes', back_populates='GoodReceivedItems')
    Variants_: Mapped['Variants'] = relationship('Variants', back_populates='GoodReceivedItems')


class Reviews(Base):
    __tablename__ = 'Reviews'
    __table_args__ = (
        ForeignKeyConstraint(['OrderDetailId'], ['OrderDetails.Id'], ondelete='CASCADE', name='FK_Reviews_OrderDetails_OrderDetailId'),
        ForeignKeyConstraint(['UserId'], ['AspNetUsers.Id'], name='FK_Reviews_AspNetUsers_UserId'),
        PrimaryKeyConstraint('Id', name='PK_Reviews'),
        Index('IX_Reviews_OrderDetailId', 'OrderDetailId'),
        Index('IX_Reviews_UserId', 'UserId')
    )

    Id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    Rating: Mapped[decimal.Decimal] = mapped_column(DECIMAL(18, 2))
    ReviewText: Mapped[str] = mapped_column(Unicode(1000, 'SQL_Latin1_General_CP1_CI_AS'), server_default=text("(N'')"))
    OrderDetailId: Mapped[uuid.UUID] = mapped_column(Uuid)
    CreatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UpdatedAt: Mapped[datetime.datetime] = mapped_column(DATETIME2)
    UserId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    OrderDetails_: Mapped['OrderDetails'] = relationship('OrderDetails', back_populates='Reviews')
    AspNetUsers_: Mapped[Optional['AspNetUsers']] = relationship('AspNetUsers', back_populates='Reviews')
