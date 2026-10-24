from datetime import date, timedelta

from backend.services.firebase_service import _get_db


def main() -> None:
    db = _get_db()
    collection = db.collection("data")
    start = date(2025, 1, 1)
    inserted = 0
    skipped = 0
    for offset in range(120):
        record_date = start + timedelta(days=offset)
        record_id = f"sample-{record_date.isoformat()}"
        doc_ref = collection.document(record_id)
        if doc_ref.get().exists:
            skipped += 1
            continue
        value = 100_000 + offset * 850 + (offset % 7) * 4_000
        doc_ref.set(
            {
                "date": record_date.isoformat(),
                "value": value,
                "memo": "합성 데모 판매 데이터",
                "created_at": record_date.isoformat(),
            }
        )
        inserted += 1
    print(f"완료: {inserted}개 추가, {skipped}개 기존 데이터 건너뜀")


if __name__ == "__main__":
    main()
