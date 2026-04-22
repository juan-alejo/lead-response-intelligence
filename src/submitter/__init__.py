"""Phase 2 — automated form submission.

Shape mirrors Phase 1: a small abstract class (`FormSubmitter`) with
interchangeable mock and real implementations behind it. The pipeline and
dashboard depend only on the abstract class.

Public surface:

    FormSubmitter       — ABC every submitter implements
    LeadIdentity        — the fake-lead contact details used to fill forms
    SubmissionRequest   — input to submit(): submission + classification + URL
    SubmissionQueue     — façade that owns the full submit-a-batch flow
    MockFormSubmitter   — deterministic submitter for demos / CI
"""

from .base import FormSubmitter, LeadIdentity, SubmissionRequest
from .mock import MockFormSubmitter
from .queue import SubmissionQueue

__all__ = [
    "FormSubmitter",
    "LeadIdentity",
    "SubmissionRequest",
    "SubmissionQueue",
    "MockFormSubmitter",
]
