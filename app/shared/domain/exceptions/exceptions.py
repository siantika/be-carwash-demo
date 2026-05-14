from typing import Any, Optional


class AppError(Exception):
    """Base exception"""

    pass


class DomainError(AppError):
    """Exception for Domain (Business)"""

    pass


# ===========================
# INFRA
# ===========================


class RepositoryError(AppError):
    """Error repository (DB, cache, dll)."""

    pass


# ===========================
# GENERIC — UNTUK KASUS BIASA
# (Gunakan ini untuk 80% kasus "not found" dan "already exists")
# ===========================


class EntityNotFound(AppError):
    """Entitas tidak ditemukan."""

    def __init__(self, entity: str, entity_id: Optional[Any] = None):
        self.entity = entity
        self.entity_id = entity_id

        super().__init__(f"{entity}")


class EntityAlreadyExists(AppError):
    """Entitas sudah ada."""

    def __init__(self, entity: str, identifier: Any = None):
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity}")


class BusinessRuleViolation(DomainError):
    """Pelanggaran aturan bisnis umum."""

    pass


class ApplicationInvariantViolation(AppError):
    """State aplikasi tidak konsisten walau input bisnis valid."""

    pass


# ===========================
# SPESIFIK — HANYA JIKA BUTUH LOGIKA BERBEDA
# ===========================


# --- Authentication ---
class InvalidPasswordError(AppError):
    """Password salah saat login."""

    pass


class InvalidTokenError(AppError):
    """Token autentikasi tidak valid, expired, atau sudah dicabut."""

    pass


class NotAuthenticatedError(InvalidTokenError):
    """Request membutuhkan token autentikasi."""

    pass


class PermissionDeniedError(AppError):
    """User terautentikasi tetapi tidak punya akses."""

    pass


class InactiveUserError(AppError):
    """User ditemukan tapi status tidak aktif."""

    pass


class AccountTemporarilyLockedError(BusinessRuleViolation):
    """Account aktif tetapi sedang terkunci sementara."""

    pass


class MissingPersistedEntityIdError(ApplicationInvariantViolation):
    """Entity yang sudah dipersist seharusnya memiliki id."""

    pass


class RevokedRefreshTokenMismatchError(ApplicationInvariantViolation):
    """Refresh token yang direvoke tidak sama dengan token yang diminta."""

    pass


class DeletedAccountMismatchError(ApplicationInvariantViolation):
    """Account yang dihapus tidak sama dengan account yang diminta."""

    pass


# --- service snapshot ---
class InvalidServiceValue(BusinessRuleViolation):
    """Kesalahan nilai pada service type (jenis layanan)"""

    pass


# ---  generic value object ---
class InvalidValueObject(DomainError):
    pass


# --- Ticket & Transaksi ---


class InvalidTicketNumber(BusinessRuleViolation):
    pass


class InvalidEntryTime(BusinessRuleViolation):
    pass


class InactiveServiceTypeCannotBeUsed(BusinessRuleViolation):
    """Service type inactive tidak boleh dipakai untuk membuat ticket."""

    pass


class InvalidTicketStateError(BusinessRuleViolation):
    """Operasi tidak valid untuk status tiket saat ini."""

    pass


class TicketNotPayableError(InvalidTicketStateError):
    """Ticket tidak berada pada status yang bisa dibayar."""

    pass


class TerminalTicketStateError(InvalidTicketStateError):
    """Status ticket terminal tidak boleh diubah lagi."""

    pass


class InvalidTargetTicketStateError(InvalidTicketStateError):
    """Target status ticket tidak valid."""

    pass


class TicketAlreadyPaidError(BusinessRuleViolation):
    """Ticket sudah memiliki transaksi pembayaran."""

    pass


class FailedToSaveTransactionError(AppError):
    """Gagal menyimpan transaksi ke database."""

    pass


class FailedToSetTicketStatusError(AppError):
    """Gagal memperbarui status tiket di database."""

    pass


# --- Service ---
class InvalidServiceKeysError(AppError):
    """Konfigurasi layanan tidak valid (missing/wrong keys)."""

    pass


class PrimaryServiceCannotBeDeactivated(BusinessRuleViolation):
    """Primary service wajib tetap aktif."""

    pass


class PrimaryServiceCannotBeDeleted(BusinessRuleViolation):
    """Primary service tidak boleh dihapus."""

    pass
