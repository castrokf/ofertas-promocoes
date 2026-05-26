from app.services.message_service import MessageInput, MessageService


def test_twitter_message_stays_short_and_factual():
    message = MessageService().twitter(
        MessageInput(
            title="SSD NVMe Kingston 1TB",
            store="Kabum",
            current_price=299,
            old_price=399,
            discount_percent=25,
            quality_label="excelente",
            link="https://example.com",
            category="ssd",
        )
    )

    assert "SSD NVMe Kingston 1TB" in message
    assert "R$ 299,00" in message
    assert len(message) <= 280
