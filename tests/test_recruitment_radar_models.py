"""M1 public recruitment-radar model contracts."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateTable

from src.db.models import (
    CampaignGraduationYear,
    Company,
    CompanyChangeEvent,
    ObservedPositionRef,
    RecruitmentCampaign,
    SourceSnapshot,
)


def _company(session, suffix: str = "") -> Company:
    company = Company(
        registry_id=f"cmb{suffix}",
        name=f"招商银行{suffix}",
        aliases=["招行", "CMB"],
        industry="金融",
        ownership_type="listed",
        status="monitoring",
        website="https://career.cmbchina.com/",
        first_verified_at=datetime(2026, 8, 5, 9, 42),
    )
    session.add(company)
    session.flush()
    return company


def _campaign(session, company: Company, suffix: str = "") -> RecruitmentCampaign:
    campaign = RecruitmentCampaign(
        company_id=company.id,
        source_id=f"cmb_campus{suffix}",
        campaign_key="2027-summer-internship",
        name="2027 届暑期实习生招聘",
        season="early",
        campaign_year=2026,
        recruitment_type="internship",
        internship_type="summer",
        graduation_years=[2027, 2028],
        status="active",
        official_url="https://career.cmbchina.com/campus/home",
        classification_confidence=0.98,
        classification_evidence={"title": "2027 届暑期实习生招聘"},
    )
    session.add(campaign)
    session.flush()
    return campaign


def _snapshot(
    session,
    company: Company,
    *,
    source_id: str = "cmb_campus",
    run_key: str | None = None,
    baseline: bool = False,
    previous_valid_snapshot_id: int | None = None,
) -> SourceSnapshot:
    snapshot = SourceSnapshot(
        company_id=company.id,
        source_id=source_id,
        run_key=run_key or (
            f"{source_id}:baseline"
            if baseline
            else f"{source_id}:after:{previous_valid_snapshot_id or 'none'}"
        ),
        previous_valid_snapshot_id=previous_valid_snapshot_id,
        status="success",
        is_baseline=baseline,
        fetched_at=datetime(2026, 8, 18, 9, 0),
        completed_at=datetime(2026, 8, 18, 9, 1),
        source_total=2,
        fetched_total=2,
        indexed_total=2,
        excluded_total=0,
        failed_total=0,
        position_keys=["publish:1", "publish:2"],
        position_set_hash="sha256:positions",
        response_hash="sha256:response",
        parser_version="cmb-campus/1",
        completeness_status="count_matched",
        comparison_status="baseline" if baseline else "compared",
    )
    session.add(snapshot)
    session.flush()
    return snapshot


def test_campaign_keeps_multiple_graduation_years_separate_from_campaign_year(session):
    company = _company(session)
    campaign = _campaign(session, company)

    session.expire_all()
    stored = session.get(RecruitmentCampaign, campaign.id)

    assert stored.campaign_year == 2026
    assert stored.graduation_years == [2027, 2028]
    assert stored.graduation_years_status == "known"
    assert stored.recruitment_type == "internship"
    assert stored.internship_type == "summer"
    assert stored.company.registry_id == "cmb"


def test_campaign_can_be_filtered_by_graduation_year_in_sql(session):
    company = _company(session)
    campaign = _campaign(session, company)

    result = session.scalars(
        select(RecruitmentCampaign)
        .join(CampaignGraduationYear)
        .where(CampaignGraduationYear.graduation_year == 2028)
    ).one()

    assert result.id == campaign.id
    assert result.graduation_years == [2027, 2028]


def test_observed_position_is_lightweight_and_keeps_unknown_classification(session):
    company = _company(session)
    campaign = _campaign(session, company)
    position = ObservedPositionRef(
        company_id=company.id,
        campaign_id=campaign.id,
        source_id="cmb_campus",
        dedupe_key="publish:abc",
        identity_kind="external_id",
        external_job_id="abc",
        canonical_url="https://career.cmbchina.com/positionDetail/school?publishId=abc",
        title="产品方向实习生",
        locations=["深圳", "上海"],
        category="unknown",
        recruitment_type="internship",
        internship_type="summer",
        graduation_years=[2027, 2028],
        content_fingerprint="sha256:light-fields",
        classification_confidence=0.4,
        classification_evidence={"reason": "岗位方向证据不足"},
    )
    session.add(position)
    session.flush()

    assert position.category == "unknown"
    assert position.locations == ["深圳", "上海"]
    assert position.graduation_years == [2027, 2028]
    assert {"jd", "description", "requirement"}.isdisjoint(
        ObservedPositionRef.__table__.columns.keys()
    )


def test_position_identity_can_fall_back_without_a_detail_url(session):
    company = _company(session)
    position = ObservedPositionRef(
        company_id=company.id,
        source_id="official_feed",
        dedupe_key="external:job-42",
        identity_kind="external_id",
        external_job_id="job-42",
        canonical_url=None,
        title="产品经理校招生",
        content_fingerprint="sha256:job-42-light-fields",
    )
    session.add(position)
    session.flush()

    assert position.canonical_url is None
    assert position.identity_kind == "external_id"


def test_position_source_key_is_idempotent_per_source(session):
    company = _company(session)
    common = {
        "company_id": company.id,
        "source_id": "cmb_campus",
        "dedupe_key": "publish:same",
        "identity_kind": "canonical_url",
        "canonical_url": "https://career.cmbchina.com/positionDetail/school?publishId=same",
        "title": "同一岗位",
        "content_fingerprint": "sha256:same",
    }
    session.add(ObservedPositionRef(**common))
    session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(ObservedPositionRef(**common))
            session.flush()


@pytest.mark.parametrize(
    "model",
    [
        lambda company_id: RecruitmentCampaign(
            company_id=company_id,
            source_id="source",
            campaign_key="bad-confidence",
            name="活动",
            season="autumn",
            recruitment_type="campus_full_time",
            internship_type="not_applicable",
            graduation_years=[2027],
            status="active",
            official_url="https://example.com/campus",
            classification_confidence=1.1,
        ),
        lambda company_id: ObservedPositionRef(
            company_id=company_id,
            source_id="source",
            dedupe_key="bad-missing-count",
            identity_kind="canonical_url",
            canonical_url="https://example.com/job/1",
            title="岗位",
            content_fingerprint="sha256:bad",
            missing_count=-1,
        ),
    ],
)
def test_model_checks_reject_invalid_classification_data(session, model):
    company = _company(session)

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(model(company.id))
            session.flush()


def test_baseline_snapshot_must_be_successful_and_reconciled(session):
    company = _company(session)
    baseline = _snapshot(session, company, baseline=True)

    assert baseline.is_baseline is True
    assert baseline.position_keys == ["publish:1", "publish:2"]
    assert baseline.change_events == []

    follow_up = _snapshot(
        session,
        company,
        previous_valid_snapshot_id=baseline.id,
    )
    assert follow_up.comparison_status == "compared"
    assert follow_up.previous_valid_snapshot.id == baseline.id

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company.id,
                    source_id="failed_source",
                    run_key="failed_source:baseline",
                    status="failed",
                    is_baseline=True,
                    parser_version="parser/1",
                    completeness_status="failed",
                    comparison_status="baseline",
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company.id,
                    source_id="mismatched_source",
                    run_key="mismatched_source:baseline",
                    status="success",
                    is_baseline=True,
                    parser_version="parser/1",
                    completeness_status="incomplete",
                    comparison_status="baseline",
                )
            )
            session.flush()


def test_snapshot_rejects_duplicate_baseline_and_invalid_comparison(session):
    company = _company(session)
    baseline = _snapshot(session, company, baseline=True)

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company.id,
                    source_id="cmb_campus",
                    run_key="cmb_campus:second-baseline",
                    status="success",
                    is_baseline=True,
                    parser_version="cmb-campus/1",
                    completeness_status="count_matched",
                    comparison_status="baseline",
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company.id,
                    source_id="cmb_campus",
                    run_key="cmb_campus:failed-compared",
                    previous_valid_snapshot_id=baseline.id,
                    status="failed",
                    is_baseline=False,
                    parser_version="cmb-campus/1",
                    completeness_status="failed",
                    comparison_status="compared",
                )
            )
            session.flush()


def test_snapshot_run_key_and_previous_comparison_are_idempotent(session):
    company = _company(session)
    baseline = _snapshot(session, company, baseline=True)
    _snapshot(
        session,
        company,
        run_key="cmb_campus:run-2",
        previous_valid_snapshot_id=baseline.id,
    )

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            _snapshot(
                session,
                company,
                run_key="cmb_campus:run-2",
                previous_valid_snapshot_id=baseline.id,
            )


def test_public_facts_cannot_cross_company_or_source_scope(session):
    company_a = _company(session, "_a")
    company_b = _company(session, "_b")
    campaign_b = _campaign(session, company_b, "_b")
    baseline_a = _snapshot(
        session,
        company_a,
        source_id="source_a",
        run_key="source_a:baseline",
        baseline=True,
    )
    baseline_b = _snapshot(
        session,
        company_b,
        source_id="source_b",
        run_key="source_b:baseline",
        baseline=True,
    )

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                ObservedPositionRef(
                    company_id=company_a.id,
                    campaign_id=campaign_b.id,
                    source_id="source_a",
                    dedupe_key="cross-company-position",
                    identity_kind="fingerprint",
                    title="不应串公司的岗位",
                    content_fingerprint="sha256:cross-company-position",
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company_a.id,
                    source_id="source_other",
                    run_key="source_other:compared",
                    previous_valid_snapshot_id=baseline_a.id,
                    status="success",
                    is_baseline=False,
                    parser_version="parser/1",
                    completeness_status="pagination_verified",
                    comparison_status="compared",
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                CompanyChangeEvent(
                    company_id=company_a.id,
                    snapshot_id=baseline_b.id,
                    source_id="source_b",
                    dedup_key="cross-company-event",
                    event_type="page_updated",
                    reporting_date_cn=date(2026, 8, 18),
                )
            )
            session.flush()


def test_monitoring_company_requires_verification_timestamp(session):
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                Company(
                    registry_id="unverified-monitoring",
                    name="未核验监控公司",
                    status="monitoring",
                )
            )
            session.flush()


def test_change_event_is_traceable_and_idempotent(session):
    company = _company(session)
    campaign = _campaign(session, company)
    baseline = _snapshot(session, company, baseline=True)
    snapshot = _snapshot(
        session,
        company,
        run_key="cmb_campus:change-run",
        previous_valid_snapshot_id=baseline.id,
    )
    event = CompanyChangeEvent(
        company_id=company.id,
        campaign_id=campaign.id,
        snapshot_id=snapshot.id,
        source_id="cmb_campus",
        dedup_key="cmb_campus:snapshot-2:positions_changed",
        event_type="positions_changed",
        added_count=2,
        closed_count=1,
        changed_count=0,
        reporting_date_cn=date(2026, 8, 18),
        occurred_at=datetime(2026, 8, 18, 9, 1),
        evidence={"added": ["publish:3", "publish:4"], "closed": ["publish:1"]},
    )
    session.add(event)
    session.flush()

    assert event.snapshot.position_set_hash == "sha256:positions"
    assert event.company.registry_id == "cmb"
    assert event.campaign.graduation_years == [2027, 2028]

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                CompanyChangeEvent(
                    company_id=company.id,
                    snapshot_id=snapshot.id,
                    source_id="cmb_campus",
                    dedup_key=event.dedup_key,
                    event_type="positions_changed",
                    added_count=2,
                    closed_count=1,
                    reporting_date_cn=date(2026, 8, 18),
                )
            )
            session.flush()


def test_snapshot_counts_and_times_must_support_a_valid_comparison(session):
    company = _company(session)

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company.id,
                    source_id="bad_counts",
                    run_key="bad_counts:baseline",
                    status="success",
                    is_baseline=True,
                    fetched_at=datetime(2026, 8, 18, 9, 0),
                    completed_at=datetime(2026, 8, 18, 9, 1),
                    source_total=10,
                    fetched_total=1,
                    indexed_total=1,
                    excluded_total=0,
                    failed_total=0,
                    position_set_hash="sha256:one",
                    parser_version="parser/1",
                    completeness_status="count_matched",
                    comparison_status="baseline",
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                SourceSnapshot(
                    company_id=company.id,
                    source_id="bad_time",
                    run_key="bad_time:baseline",
                    status="success",
                    is_baseline=True,
                    fetched_at=datetime(2026, 8, 18, 9, 1),
                    completed_at=datetime(2026, 8, 18, 9, 0),
                    source_total=1,
                    fetched_total=1,
                    indexed_total=1,
                    position_set_hash="sha256:one",
                    parser_version="parser/1",
                    completeness_status="count_matched",
                    comparison_status="baseline",
                )
            )
            session.flush()


def test_position_lifecycle_times_are_consistent(session):
    company = _company(session)

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                ObservedPositionRef(
                    company_id=company.id,
                    source_id="official",
                    dedupe_key="closed-without-time",
                    identity_kind="fingerprint",
                    title="已关闭岗位",
                    status="closed",
                    closed_at=None,
                    content_fingerprint="sha256:closed",
                )
            )
            session.flush()


@pytest.mark.parametrize(
    "event_type, counts",
    [
        ("positions_changed", {}),
        ("position_reopened", {"added_count": 1, "reopened_count": 1}),
        ("page_updated", {"changed_count": 1}),
    ],
)
def test_change_event_type_and_counts_cannot_conflict(
    session, event_type, counts
):
    company = _company(session)
    baseline = _snapshot(session, company, baseline=True)

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                CompanyChangeEvent(
                    company_id=company.id,
                    snapshot_id=baseline.id,
                    source_id="cmb_campus",
                    dedup_key=f"invalid:{event_type}",
                    event_type=event_type,
                    reporting_date_cn=date(2026, 8, 18),
                    **counts,
                )
            )
            session.flush()


def test_public_models_compile_for_sqlite_and_postgresql():
    tables = [
        RecruitmentCampaign.__table__,
        CampaignGraduationYear.__table__,
        ObservedPositionRef.__table__,
        SourceSnapshot.__table__,
        CompanyChangeEvent.__table__,
    ]

    for table in tables:
        sqlite_ddl = str(CreateTable(table).compile(dialect=sqlite.dialect()))
        postgres_ddl = str(
            CreateTable(table).compile(dialect=postgresql.dialect())
        )
        assert f"CREATE TABLE {table.name}" in sqlite_ddl
        assert f"CREATE TABLE {table.name}" in postgres_ddl
