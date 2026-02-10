from application.use_cases.ticket.create_ticket_usecase import GenerateEan13TimeBased


def is_valid_ean13(code: str) -> bool:
    if not isinstance(code, str) or len(code) != 13 or not code.isdigit():
        return False

    digits = [int(c) for c in code]
    check = digits[-1]
    first12 = digits[:12]

    # EAN-13 checksum:
    # sum(odd positions) + 3*sum(even positions), positions counted from 1
    s_odd = sum(first12[0::2])   # pos 1,3,5,7,9,11
    s_even = sum(first12[1::2])  # pos 2,4,6,8,10,12
    total = s_odd + 3 * s_even

    expected = (10 - (total % 10)) % 10
    return check == expected


def test_generated_barcode_should_be_valid_ean13():
    gen = GenerateEan13TimeBased()
    code = gen.generate()  

    assert len(code) == 13
    assert code.isdigit()
    assert is_valid_ean13(code), f"Not valid EAN-13: {code}"
