# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import or_

from passlib.context import CryptContext
from app.db import SessionLocal
from app.models.business import Business
from app.models.business_service import BusinessService
from app.models.review import Review
from app.models.service import Service
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.workorder import WorkOrder, WorkOrderStatus


def log(message: str) -> None:
    print(f"[seed-demo] {message}")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_demo_password(password: str) -> str:
    return pwd_context.hash(password)

def upsert_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
) -> tuple[User, str]:
    user = db.query(User).filter(User.email == email).first()
    password_hash = hash_demo_password(password)

    if user:
        changed = False
        if user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if user.role != role:
            user.role = role
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if user.password_hash != password_hash:
            user.password_hash = password_hash
            changed = True

        return user, "updated" if changed else "reused"

    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user, "created"


def upsert_business(
    db: Session,
    *,
    owner_id: int,
    name: str,
    description: str,
    address: str,
    phone: str,
) -> tuple[Business, str]:
    business = (
        db.query(Business)
        .filter(Business.owner_id == owner_id, Business.name == name)
        .first()
    )

    if business:
        changed = False
        if business.description != description:
            business.description = description
            changed = True
        if business.address != address:
            business.address = address
            changed = True
        if business.phone != phone:
            business.phone = phone
            changed = True
        if not business.is_active:
            business.is_active = True
            changed = True
        return business, "updated" if changed else "reused"

    business = Business(
        owner_id=owner_id,
        name=name,
        description=description,
        address=address,
        phone=phone,
        is_active=True,
    )
    db.add(business)
    db.flush()
    return business, "created"


def upsert_vehicle(
    db: Session,
    *,
    owner_id: int,
    plate: str,
    make: str,
    model: str,
    year: int,
) -> tuple[Vehicle, str]:
    vehicle = db.query(Vehicle).filter(Vehicle.plate == plate).first()

    if vehicle:
        changed = False
        if vehicle.owner_id != owner_id:
            vehicle.owner_id = owner_id
            changed = True
        if vehicle.make != make:
            vehicle.make = make
            changed = True
        if vehicle.model != model:
            vehicle.model = model
            changed = True
        if vehicle.year != year:
            vehicle.year = year
            changed = True
        return vehicle, "updated" if changed else "reused"

    vehicle = Vehicle(
        owner_id=owner_id,
        plate=plate,
        make=make,
        model=model,
        year=year,
    )
    db.add(vehicle)
    db.flush()
    return vehicle, "created"


SERVICE_CATALOG_TARGETS: list[tuple[str, str]] = [
    ("Yağ Değişimi", "Motor yağı ve yağ filtresinin üretici standartlarına uygun yenilenmesi."),
    ("Fren Bakımı", "Balata, disk ve fren hidrolik sistemi kontrolü ile gerekli bakım işlemleri."),
    ("Periyodik Bakım", "Kilometre ve araç yaşına uygun periyodik bakım paketi."),
    ("Akü Kontrolü", "Akü sağlık testi, şarj sistemi kontrolü ve kutup başı temizliği."),
    ("Lastik Değişimi", "Mevsime uygun lastik sökme-takma ve hava basıncı kontrolü."),
    ("Rot Balans", "Ön düzen geometrisi kontrolü ve balans ayar işlemleri."),
    ("Motor Arıza Tespiti", "OBD cihazı ile arıza kodu okuma ve temel motor diagnostik kontrolü."),
]

SERVICE_MINIMUM_PRICES: dict[str, Decimal] = {
    "Yağ Değişimi": Decimal("1800"),
    "Fren Bakımı": Decimal("2500"),
    "Periyodik Bakım": Decimal("3500"),
    "Akü Kontrolü": Decimal("900"),
    "Lastik Değişimi": Decimal("1200"),
    "Rot Balans": Decimal("1500"),
    "Motor Arıza Tespiti": Decimal("1000"),
}


def ensure_service_catalog(db: Session) -> list[Service]:
    ensured: list[Service] = []

    for name, description in SERVICE_CATALOG_TARGETS:
        service = db.query(Service).filter(Service.name == name).first()

        if service:
            changed = False
            if service.description != description:
                service.description = description
                changed = True
            if not service.is_active:
                service.is_active = True
                changed = True
            print_action("Servis", "updated" if changed else "reused", name)
        else:
            service = Service(
                name=name,
                description=description,
                is_active=True,
            )
            db.add(service)
            db.flush()
            print_action("Servis", "created", name)

        ensured.append(service)

    return ensured


def cleanup_demo_scope(
    db: Session,
    *,
    demo_customer_id: int,
    demo_business_id: int,
) -> None:
    workorder_ids = [
        row[0]
        for row in (
            db.query(WorkOrder.id)
            .filter(
                or_(
                    WorkOrder.business_id == demo_business_id,
                    WorkOrder.customer_id == demo_customer_id,
                )
            )
            .all()
        )
    ]

    review_query = db.query(Review).filter(
        or_(
            Review.business_id == demo_business_id,
            Review.customer_id == demo_customer_id,
            Review.workorder_id.in_(workorder_ids) if workorder_ids else False,
        )
    )
    deleted_reviews = review_query.delete(synchronize_session=False)
    log(f"Temizlik(reviews): {deleted_reviews} kayıt silindi.")

    deleted_workorders = (
        db.query(WorkOrder)
        .filter(
            or_(
                WorkOrder.business_id == demo_business_id,
                WorkOrder.customer_id == demo_customer_id,
            )
        )
        .delete(synchronize_session=False)
    )
    log(f"Temizlik(workorders): {deleted_workorders} kayıt silindi.")

    deleted_business_services = (
        db.query(BusinessService)
        .filter(BusinessService.business_id == demo_business_id)
        .delete(synchronize_session=False)
    )
    log(f"Temizlik(business_services): {deleted_business_services} kayıt silindi.")

    deleted_vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.owner_id == demo_customer_id)
        .delete(synchronize_session=False)
    )
    log(f"Temizlik(vehicles): {deleted_vehicles} kayıt silindi.")


def upsert_business_service(
    db: Session,
    *,
    business_id: int,
    service_id: int,
    minimum_price: Decimal,
) -> tuple[BusinessService, str]:
    item = (
        db.query(BusinessService)
        .filter(
            BusinessService.business_id == business_id,
            BusinessService.service_id == service_id,
        )
        .first()
    )

    if item:
        changed = False
        if item.minimum_price != minimum_price:
            item.minimum_price = minimum_price
            changed = True
        if not item.is_active:
            item.is_active = True
            changed = True
        return item, "updated" if changed else "reused"

    item = BusinessService(
        business_id=business_id,
        service_id=service_id,
        minimum_price=minimum_price,
        is_active=True,
    )
    db.add(item)
    db.flush()
    return item, "created"


def upsert_work_order(
    db: Session,
    *,
    customer_id: int,
    vehicle_id: int,
    business_id: int,
    service_type: str,
    estimated_price: Decimal,
    status: WorkOrderStatus,
    description: str,
) -> tuple[WorkOrder, str]:
    existing = (
        db.query(WorkOrder)
        .filter(
            WorkOrder.customer_id == customer_id,
            WorkOrder.vehicle_id == vehicle_id,
            WorkOrder.business_id == business_id,
            WorkOrder.service_type == service_type,
            WorkOrder.estimated_price == estimated_price,
            WorkOrder.status == status,
        )
        .first()
    )

    if existing:
        changed = False
        if existing.description != description:
            existing.description = description
            changed = True

        if status in {WorkOrderStatus.delivered, WorkOrderStatus.ready_for_delivery}:
            if existing.completed_at is None:
                existing.completed_at = datetime.utcnow()
                changed = True
        elif existing.completed_at is not None:
            existing.completed_at = None
            changed = True

        return existing, "updated" if changed else "reused"

    completed_at = None
    if status in {WorkOrderStatus.delivered, WorkOrderStatus.ready_for_delivery}:
        completed_at = datetime.utcnow()

    work_order = WorkOrder(
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        business_id=business_id,
        service_type=service_type,
        description=description,
        estimated_price=estimated_price,
        status=status,
        completed_at=completed_at,
    )
    db.add(work_order)
    db.flush()
    return work_order, "created"


def upsert_review(
    db: Session,
    *,
    workorder_id: int,
    customer_id: int,
    business_id: int,
    rating: int,
    comment: str,
) -> tuple[Review, str]:
    review = db.query(Review).filter(Review.workorder_id == workorder_id).first()

    if review:
        changed = False
        if review.customer_id != customer_id:
            review.customer_id = customer_id
            changed = True
        if review.business_id != business_id:
            review.business_id = business_id
            changed = True
        if review.rating != rating:
            review.rating = rating
            changed = True
        if review.comment != comment:
            review.comment = comment
            changed = True
        return review, "updated" if changed else "reused"

    review = Review(
        workorder_id=workorder_id,
        customer_id=customer_id,
        business_id=business_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    db.flush()
    return review, "created"


def print_action(entity: str, action: str, identifier: str) -> None:
    action_text = {
        "created": "oluşturuldu",
        "updated": "güncellendi",
        "reused": "yeniden kullanıldı",
    }.get(action, action)
    log(f"{entity}: {identifier} -> {action_text}")


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        log("Demo veri hazırlığı başlıyor...")

        customer, action = upsert_user(
            db,
            email="demo.customer@example.com",
            password="Demo12345",
            full_name="Ayşe Yılmaz",
            role=UserRole.customer,
        )
        print_action("Kullanıcı(customer)", action, customer.email)

        owner, action = upsert_user(
            db,
            email="demo.owner@example.com",
            password="Demo12345",
            full_name="Mehmet Usta",
            role=UserRole.business_owner,
        )
        print_action("Kullanıcı(owner)", action, owner.email)

        # Admin rolü modelde destekleniyorsa oluşturulur; beklenmeyen bir durumda atlanır.
        admin = None
        try:
            admin, action = upsert_user(
                db,
                email="demo.admin@example.com",
                password="Demo12345",
                full_name="Elif Admin",
                role=UserRole.admin,
            )
            print_action("Kullanıcı(admin)", action, admin.email)
        except Exception as admin_error:
            log(f"Admin kullanıcı atlandı: {admin_error}")

        business, action = upsert_business(
            db,
            owner_id=owner.id,
            name="Çanakkale Oto Servis",
            description=(
                "Periyodik bakım, fren ve motor sistemleri için güvenilir bakım-onarım hizmeti "
                "sunan, süreç takibini dijital ortamdan görünür kılan yerel oto servis işletmesi."
            ),
            address="Küçük Sanayi Sitesi, Çanakkale",
            phone="0286 000 00 00",
        )
        print_action("İşletme", action, business.name)

        cleanup_demo_scope(
            db,
            demo_customer_id=customer.id,
            demo_business_id=business.id,
        )

        vehicle, action = upsert_vehicle(
            db,
            owner_id=customer.id,
            plate="17 ABC 123",
            make="Renault",
            model="Clio",
            year=2017,
        )
        print_action("Araç", action, vehicle.plate)

        selected_services = ensure_service_catalog(db)

        selected_services_by_name = {service.name: service for service in selected_services}

        missing_price_services = [
            service_name
            for service_name in selected_services_by_name
            if service_name not in SERVICE_MINIMUM_PRICES
        ]
        if missing_price_services:
            raise RuntimeError(
                "Minimum fiyatı tanımlanmamış servisler bulundu: "
                + ", ".join(missing_price_services)
            )

        for service_name, min_price in SERVICE_MINIMUM_PRICES.items():
            service = selected_services_by_name[service_name]
            _, action = upsert_business_service(
                db,
                business_id=business.id,
                service_id=service.id,
                minimum_price=min_price,
            )
            print_action("BusinessService", action, f"{business.name} / {service.name}")

        workorder_specs = [
            {
                "service_type": "Periyodik Bakım",
                "estimated_price": Decimal("4100"),
                "status": WorkOrderStatus.delivered,
                "description": "Periyodik bakım tamamlandı, filtre ve sıvı kontrolleri sonrası araç teslim edildi.",
            },
            {
                "service_type": "Fren Bakımı",
                "estimated_price": Decimal("3200"),
                "status": WorkOrderStatus.delivered,
                "description": "Fren balata ve disk kontrolleri yapıldı, gerekli değişimler sonrası araç teslim edildi.",
            },
            {
                "service_type": "Yağ Değişimi",
                "estimated_price": Decimal("1900"),
                "status": WorkOrderStatus.delivered,
                "description": "Yağ değişimi ve genel güvenlik kontrolü tamamlandı, araç teslim edildi.",
            },
            {
                "service_type": "Rot Balans",
                "estimated_price": Decimal("1700"),
                "status": WorkOrderStatus.delivered,
                "description": "Rot ayarı ve balans işlemleri tamamlandı, test sürüşü sonrası teslim edildi.",
            },
            {
                "service_type": "Lastik Değişimi",
                "estimated_price": Decimal("1400"),
                "status": WorkOrderStatus.ready_for_delivery,
                "description": "Mevsim lastiği değişimi tamamlandı, araç son kontrol sonrası teslime hazır.",
            },
            {
                "service_type": "Motor Arıza Tespiti",
                "estimated_price": Decimal("1300"),
                "status": WorkOrderStatus.repair,
                "description": "Arıza kodu analiz edildi, parça temini sonrası onarım süreci devam ediyor.",
            },
            {
                "service_type": "Akü Kontrolü",
                "estimated_price": Decimal("950"),
                "status": WorkOrderStatus.inspection,
                "description": "Akü şarj-deşarj ölçümleri ve alternatör kontrolü için inceleme aşamasında.",
            },
            {
                "service_type": "Periyodik Bakım",
                "estimated_price": Decimal("3600"),
                "status": WorkOrderStatus.received,
                "description": "Yeni periyodik bakım kaydı açıldı, araç kabulü yapıldı.",
            },
        ]

        created_or_existing_workorders: list[WorkOrder] = []
        for spec in workorder_specs:
            workorder, action = upsert_work_order(
                db,
                customer_id=customer.id,
                vehicle_id=vehicle.id,
                business_id=business.id,
                service_type=spec["service_type"],
                estimated_price=spec["estimated_price"],
                status=spec["status"],
                description=spec["description"],
            )
            created_or_existing_workorders.append(workorder)
            print_action(
                "İş Emri",
                action,
                f"{workorder.service_type} / {workorder.estimated_price} / {workorder.status.value}",
            )

        delivered_workorders = [
            wo for wo in created_or_existing_workorders if wo.status == WorkOrderStatus.delivered
        ]

        if len(delivered_workorders) < 4:
            raise RuntimeError("Yorumlar için en az 4 delivered iş emri oluşturulamadı.")

        review_targets: Iterable[tuple[WorkOrder, int, str]] = [
            (
                delivered_workorders[0],
                4,
                "Periyodik bakım için gittim. İşlem süreci sistemden düzenli takip edilebildi, araç teslimi zamanında yapıldı.",
            ),
            (
                delivered_workorders[1],
                5,
                "Fren balataları değiştirildi. İşlem öncesi tahmini fiyat ve durum bilgisi netti.",
            ),
            (
                delivered_workorders[2],
                5,
                "Yağ değişimi ve genel kontrol için hizmet aldım. Aracın hangi aşamada olduğunu görebilmek güven verdi.",
            ),
            (
                delivered_workorders[3],
                4,
                "Rot balans işlemi beklediğimden hızlı tamamlandı. Teslim süreci ve bilgilendirme yeterliydi.",
            ),
        ]

        for workorder, rating, comment in review_targets:
            _, action = upsert_review(
                db,
                workorder_id=workorder.id,
                customer_id=customer.id,
                business_id=business.id,
                rating=rating,
                comment=comment,
            )
            print_action("Yorum", action, f"workorder_id={workorder.id}")

        db.commit()

        log("Demo veri işlemi başarıyla tamamlandı.")
        log(f"Customer: {customer.email}")
        log(f"Owner: {owner.email}")
        if admin is not None:
            log(f"Admin: {admin.email}")
        log(f"İşletme: {business.name} (id={business.id})")
        log(f"Araç: {vehicle.plate} (id={vehicle.id})")

    except Exception as error:
        db.rollback()
        log("Hata oluştu, tüm değişiklikler geri alındı.")
        log(f"Hata detayı: {error}")
        raise
    finally:
        db.close()
        log("DB session kapatıldı.")


if __name__ == "__main__":
    seed_demo_data()
