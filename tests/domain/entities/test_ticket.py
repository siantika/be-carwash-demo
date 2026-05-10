import pytest

from domain.entities.ticket import Ticket, TicketStatusEnum
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


class DummyEntryTime:
    pass

class DummyServiceSnapshot:
    pass

class DummyTicketNumber:
    pass


def make_ticket(status: TicketStatusEnum = TicketStatusEnum.IN_PROGRESS) -> Ticket:
    return Ticket(
        service_type_id=1,
        service_snapshot=DummyServiceSnapshot(),
        ticket_number=DummyTicketNumber(),
        entry_time=DummyEntryTime(),
        status=status,
    )


def test_ticket_default_status_is_in_progress():
    t = make_ticket()  
    assert t.status == TicketStatusEnum.IN_PROGRESS


@pytest.mark.parametrize(
    "target",
    [TicketStatusEnum.PAID, TicketStatusEnum.VOID],
)
def test_change_status_from_in_progress_allowed(target):
    t = make_ticket(TicketStatusEnum.IN_PROGRESS)
    t.change_status(target)
    assert t.status == target


@pytest.mark.parametrize(
    "terminal_status",
    [TicketStatusEnum.PAID, TicketStatusEnum.VOID],
)
def test_change_status_from_terminal_state_raises(terminal_status):
    t = make_ticket(status=terminal_status)

    with pytest.raises(BusinessRuleViolation) as exc:
        t.change_status(TicketStatusEnum.IN_PROGRESS)

    assert "terminal state" in str(exc.value)


def test_mark_paid_sets_status_paid():
    t = make_ticket(TicketStatusEnum.IN_PROGRESS)
    t.mark_paid()
    assert t.status == TicketStatusEnum.PAID


def test_mark_void_sets_status_void():
    t = make_ticket(TicketStatusEnum.IN_PROGRESS)
    t.mark_void()
    assert t.status == TicketStatusEnum.VOID


def test_mark_paid_when_already_paid_raises():
    t = make_ticket(TicketStatusEnum.PAID)

    with pytest.raises(BusinessRuleViolation):
        t.mark_paid()


def test_mark_void_when_already_void_raises():
    t = make_ticket(TicketStatusEnum.VOID)

    with pytest.raises(BusinessRuleViolation):
        t.mark_void()

