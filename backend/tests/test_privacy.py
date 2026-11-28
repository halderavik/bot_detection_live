"""Personal details kept out of storage and the text check (app/utils/privacy.py)."""
import pytest

from app.utils.privacy import is_personal_question, mask_personal, strip_url


@pytest.mark.parametrize("url, expected", [
    ("https://survey.example.com/survey/selfserve/53b/250101?psid=abc123&email=a@b.com#q5",
     "https://survey.example.com/survey/selfserve/53b/250101"),
    ("https://survey.example.com/s/1", "https://survey.example.com/s/1"),
    ("not a url?id=7", "not a url"),
    ("", ""),
    (None, None),
])
def test_strip_url_drops_query_and_fragment(url, expected):
    assert strip_url(url) == expected


@pytest.mark.parametrize("text", [
    "What is your email address?",
    "Please enter your first name",
    "Last name",
    "Your phone number (we will only call about this study)",
    "What is your ZIP code?",
    "Please enter your postcode",
    "Street address",
    "Date of birth",
])
def test_contact_and_identity_questions_are_personal(text):
    assert is_personal_question(text)


@pytest.mark.parametrize("text", [
    "Name three brands you know",
    "What do you like about your phone?",
    "How do you feel about email marketing?",
    "Why did you choose this brand?",
    "Which issues should the company address first?",
])
def test_ordinary_open_ends_are_not_personal(text):
    assert not is_personal_question(text)


def test_box_named_email_is_personal_whatever_the_wording():
    assert is_personal_question("Q12", "email")
    assert not is_personal_question("Q12", "Q12")


def test_mask_personal_replaces_emails_and_phone_numbers():
    text = "Write to jane.doe@example.com or call +1 (416) 555-0199, I spent 1,200 dollars in 2024."
    masked = mask_personal(text)
    assert "jane.doe" not in masked and "555-0199" not in masked
    assert masked == "Write to [email] or call [phone], I spent 1,200 dollars in 2024."


def test_mask_personal_leaves_short_numbers_and_empty_text():
    assert mask_personal("I rate it 7 out of 10, about 3-4 times a week") == "I rate it 7 out of 10, about 3-4 times a week"
    assert mask_personal("") == ""
    assert mask_personal(None) is None
