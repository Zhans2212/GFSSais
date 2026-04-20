def resolve(knp: str, typ: str | None):
    knp = str(knp or "").zfill(3)
    typ = (typ or "").strip()

    if knp == "026" and typ == "СЗ":
        return "026", "026_sz"

    if knp == "026" and typ == "О":
        return "026", "026_bt"

    if knp == "026":
        return "026", "026"

    if knp == "094" and typ == "СЗ":
        return "094", "094_sz"

    if knp == "094" and typ == "О":
        return "094", "094_bt"

    if knp == "094":
        return "094", "094_penalty"

    return None, None

def build_order_report(rows):
    agg = {
        "026": {
            "026": {"count": 0, "amount": 0.0},
            "026_bt": {"count": 0, "amount": 0.0},
            "026_sz": {"count": 0, "amount": 0.0},
        },
        "094": {
            "094_penalty": {"count": 0, "amount": 0.0},
            "094_bt": {"count": 0, "amount": 0.0},
            "094_sz": {"count": 0, "amount": 0.0},
        }
    }

    for amount, count, knp, typ in rows:
        group, key = resolve(knp, typ)
        if not group:
            continue

        agg[group][key]["count"] += int(count or 0)
        agg[group][key]["amount"] += float(amount or 0)

    table_rows = [
        {
            "ttk": "026",
            "total_count": (
                agg["026"]["026"]["count"]
                + agg["026"]["026_sz"]["count"]
                + agg["026"]["026_bt"]["count"]
            ),
            "total_amount": (
                agg["026"]["026"]["amount"]
                + agg["026"]["026_sz"]["amount"]
                + agg["026"]["026_bt"]["amount"]
            ),
            "part_026_count": agg["026"]["026"]["count"],
            "part_026_amount": agg["026"]["026"]["amount"],
            "part_094_count": 0,
            "part_094_amount": 0,
            "part_bt_count": agg["026"]["026_bt"]["count"],
            "part_bt_amount": agg["026"]["026_bt"]["amount"],
            "part_sz_count": agg["026"]["026_sz"]["count"],
            "part_sz_amount": agg["026"]["026_sz"]["amount"],
        },
        {
            "ttk": "094",
            "total_count": (
                agg["094"]["094_penalty"]["count"]
                + agg["094"]["094_bt"]["count"]
                + agg["094"]["094_sz"]["count"]
            ),
            "total_amount": (
                agg["094"]["094_penalty"]["amount"]
                + agg["094"]["094_bt"]["amount"]
                + agg["094"]["094_sz"]["amount"]
            ),
            "part_026_count": 0,
            "part_026_amount": 0,
            "part_094_count": agg["094"]["094_penalty"]["count"],
            "part_094_amount": agg["094"]["094_penalty"]["amount"],
            "part_bt_count": agg["094"]["094_bt"]["count"],
            "part_bt_amount": agg["094"]["094_bt"]["amount"],
            "part_sz_count": agg["094"]["094_sz"]["count"],
            "part_sz_amount": agg["094"]["094_sz"]["amount"],
        }
    ]

    total_row = {
        "ttk": "Барлығы",
        "total_count": sum(r["total_count"] for r in table_rows),
        "total_amount": sum(r["total_amount"] for r in table_rows),
    }

    return {
        "rows": table_rows,
        "total": total_row,
    }