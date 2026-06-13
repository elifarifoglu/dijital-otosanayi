# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from app.auth import hash_password
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


def upsert_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
) -> tuple[User, str]:
    user = db.query(User).filter(User.email == email).first()
    password_hash = hash_password(password)

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


def choose_services(db: Session) -> list[Service]:
    desired_names = [
        "Periyodik Bakım",
        "Fren Balata Değişimi",
        "Motor Arıza Tespiti",
    ]

    active_services = (
        db.query(Service)
        .filter(Service.is_active.is_(True))
        .order_by(Service.id.asc())
        .all()
    )
    if not active_services:
        raise RuntimeError("Aktif servis bulunamadı. Önce migration/seeding servis verisini doğrulayın.")

    active_by_name = {service.name: service for service in active_services}

    if all(name in active_by_name for name in desired_names):
        selected = [active_by_name[name] for name in desired_names]
        log("İstenen servis adları birebir bulundu, bunlar kullanılacak.")
        return selected

    log("İstenen servis adları birebir bulunamadı. Aktif servisler:")
    for service in active_services:
        log(f"- {service.name}")

    selected = active_services[:3]
    if len(selected) < 3:
        raise RuntimeError("En az 3 aktif servis gerekli.")

    log("İlk 3 aktif servis fallback olarak kullanılacak.")
    return selected


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
                "Periyodik bakım, fren sistemi, motor arıza tespiti ve teslim süreci takibi "
                "sunan yerel oto servis işletmesi."
            ),
            address="Küçük Sanayi Sitesi, Çanakkale",
            phone="0286 000 00 00",
        )
        print_action("İşletme", action, business.name)

        vehicle, action = upsert_vehicle(
            db,
            owner_id=customer.id,
            plate="17 ABC 123",
            make="Renault",
            model="Clio",
            year=2017,
        )
        print_action("Araç", action, vehicle.plate)

        selected_services = choose_services(db)

        target_prices = [Decimal("2200"), Decimal("1700"), Decimal("1000")]
        for service, min_price in zip(selected_services, target_prices):
            _, action = upsert_business_service(
                db,
                business_id=business.id,
                service_id=service.id,
                minimum_price=min_price,
            )
            print_action("BusinessService", action, f"{business.name} / {service.name}")

        service_name_1 = selected_services[0].name
        service_name_2 = selected_services[1].name
        service_name_3 = selected_services[2].name

        workorder_specs = [
            {
                "service_type": service_name_1,
                "estimated_price": Decimal("2500"),
                "status": WorkOrderStatus.delivered,
                "description": "Periyodik bakım işlemi tamamlandı ve araç teslim edildi.",
            },
            {
                "service_type": service_name_1,
                "estimated_price": Decimal("2800"),
                "status": WorkOrderStatus.delivered,
                "description": "Periyodik bakım kapsamında filtre ve sıvı kontrolleri yapıldı.",
            },
            {
                "service_type": service_name_2,
                "estimated_price": Decimal("1800"),
                "status": WorkOrderStatus.ready_for_delivery,
                "description": "Fren sistemi parçaları değiştirildi, teslime hazır.",
            },
            {
                "service_type": service_name_3,
                "estimated_price": Decimal("1200"),
                "status": WorkOrderStatus.repair,
                "description": "Motor arıza tespiti sonrası onarım süreci devam ediyor.",
            },
            {
                "service_type": "Genel Kontrol",
                "estimated_price": Decimal("900"),
                "status": WorkOrderStatus.received,
                "description": "Genel kontrol için araç kabul edildi.",
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

        # En az 2 yorum: farklı iş emri, müşteri-işletme eşleşmesi tutarlı.
        review_targets: Iterable[tuple[WorkOrder, int, str]] = [
            (
                created_or_existing_workorders[0],
                5,
                "Aracımın bakım süreci düzenli şekilde takip edilebildi.",
            ),
            (
                created_or_existing_workorders[1],
                4,
                "Fiyat bilgisi ve işlem durumu açık şekilde gösterildi.",
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
