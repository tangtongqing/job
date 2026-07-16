"""Deterministic demo data must be substantial and honestly labelled."""

from src.db.demo_data import seed_demo_data
from src.db.models import CrawlLog, Job


def test_demo_seed_has_complete_jobs_and_honest_log(session):
    result = seed_demo_data(session, replace=True)
    jobs = session.query(Job).all()

    assert result["jobs"] >= 24
    assert len(jobs) == result["jobs"]
    assert all(job.source == "demo_snapshot" for job in jobs)
    assert all(job.jd and len(job.jd) >= 180 for job in jobs)
    assert all(job.requirement and len(job.requirement) >= 100 for job in jobs)
    assert all(job.apply_url and job.apply_url.startswith("https://") for job in jobs)
    assert all(job.source_url and job.source_url.startswith("https://") for job in jobs)
    assert all(job.education and job.experience for job in jobs)
    assert all(job.last_verified_at for job in jobs)

    logs = session.query(CrawlLog).all()
    assert len(logs) == 1
    assert logs[0].source == "demo_snapshot"
    assert logs[0].status == "skipped"
    assert "不代表真实网络采集" in (logs[0].error or "")
