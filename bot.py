import os
import asyncio
import logging
import requests
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

WHATSAPP_URL = "https://wa.me/919932382732"
TELEGRAM_SUPPORT = "https://t.me/DigitalArjun02"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Admin access
ADMIN_IDS = {8672422283, 6892918791}
ADMIN_ID = next(iter(ADMIN_IDS))

def is_admin(user_id):
    return user_id in ADMIN_IDS


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F4CA Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Products", callback_data="admin_products"),
         InlineKeyboardButton("🎁 Offers", callback_data="admin_offers")],
        [InlineKeyboardButton("?? Orders", callback_data="admin_orders")],
        [InlineKeyboardButton("?? Customers", callback_data="admin_customers"),
         InlineKeyboardButton("?? Support Tickets", callback_data="admin_support")],
    ])


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.effective_message.reply_text(
            "? Access Denied!\n\n"
            "You are not an admin. Only authorized administrators "
            "can access the BN Tech Admin Panel."
        )
        return
    context.user_data.pop("admin_input", None)
    await update.effective_message.reply_text(
        "\U0001F510 BN TECH ADMIN PANEL\n\nChoose an option:",
        reply_markup=admin_menu(),
    )


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
LANGUAGES = {
    "en": {
        "products": "\U0001F6CD Shop Products",
        "offers": "\U0001F381 Offers",
        "account": "\U0001F464 My Account",
        "orders": "\U0001F4E6 My Orders",
        "language": "\U0001F310 Language",
        "whatsapp": "WhatsApp Support",
        "telegram": "Telegram Support",
        "welcome": "\U0001F44B Welcome to BN Tech Bot!",
        "intro": "\U0001F680 Explore digital products and services.",
        "prices": "\U0001F1EE\U0001F1F3 India: INR | International: USDT",
        "choose": "Choose an option below:",
        "account_title": "\U0001F464 My Account",
        "name": "Name", "username": "Username", "telegram_id": "Telegram ID",
        "orders_hint": "Use My Orders to check your orders.",
        "orders_title": "\U0001F4E6 My Orders",
        "no_orders": "No order is linked to your Telegram account yet.",
        "recent_orders": "\U0001F4CB Your Recent Orders",
        "load_error": "Orders could not be loaded. Please try again later.",
        "setup_error": "Order setup is incomplete. Please contact support.",
        "language_title": "\U0001F310 Choose your language:",
        "language_saved": "Language changed to English.",
        "order": "Order", "product_id": "Product ID", "quantity": "Quantity",
        "total": "Total", "status": "Status", "date": "Date",
    },
    "hi": {
        "products": "\U0001F6CD Products Dekhein",
        "offers": "\U0001F381 Offers",
        "account": "\U0001F464 Mera Account",
        "orders": "\U0001F4E6 Mere Orders",
        "language": "\U0001F310 Bhasha",
        "whatsapp": "WhatsApp Support",
        "telegram": "Telegram Support",
        "welcome": "BN Tech Bot mein aapka swagat hai!",
        "intro": "Digital products aur services explore karein.",
        "prices": "India: INR | International: USDT",
        "choose": "Neeche se ek option chunein:",
        "account_title": "Mera Account",
        "name": "Naam", "username": "Username", "telegram_id": "Telegram ID",
        "orders_hint": "Apne orders dekhne ke liye Mere Orders chunein.",
        "orders_title": "Mere Orders",
        "no_orders": "Aapke Telegram account se abhi koi order linked nahi hai.",
        "recent_orders": "Aapke Recent Orders",
        "load_error": "Orders load nahi hue. Baad mein dobara try karein.",
        "setup_error": "Order setup adhura hai. Support se sampark karein.",
        "language_title": "Apni bhasha chunein:",
        "language_saved": "Bhasha Hindi mein set ho gayi.",
        "order": "Order", "product_id": "Product ID", "quantity": "Quantity",
        "total": "Kul", "status": "Status", "date": "Tarikh",
    },
    "bn": {
        "products": "\U0001F6CD Products Dekhun",
        "offers": "\U0001F381 Offers",
        "account": "\U0001F464 Amar Account",
        "orders": "\U0001F4E6 Amar Orders",
        "language": "\U0001F310 Bhasha",
        "whatsapp": "WhatsApp Support",
        "telegram": "Telegram Support",
        "welcome": "BN Tech Bot-e swagat!",
        "intro": "Digital products ebong services dek hun.",
        "prices": "India: INR | International: USDT",
        "choose": "Nicher theke ekta option bachun:",
        "account_title": "Amar Account",
        "name": "Naam", "username": "Username", "telegram_id": "Telegram ID",
        "orders_hint": "Orders dekhte Amar Orders bachun.",
        "orders_title": "Amar Orders",
        "no_orders": "Apnar Telegram account-e ekhono kono order nei.",
        "recent_orders": "Apnar Recent Orders",
        "load_error": "Orders load hoyni. Pore abar cheshta korun.",
        "setup_error": "Order setup shompurno noy. Support-e jogajog korun.",
        "language_title": "Apnar bhasha bachun:",
        "language_saved": "Bhasha Bangla-te set hoyeche.",
        "order": "Order", "product_id": "Product ID", "quantity": "Quantity",
        "total": "Mot", "status": "Status", "date": "Tarikh",
    },
}

def user_language(context):
    lang = context.user_data.get("language", "en") if context else "en"
    return lang if lang in LANGUAGES else "en"

def tr(context, key):
    return LANGUAGES[user_language(context)].get(key, LANGUAGES["en"].get(key, key))

def main_menu(lang="en"):
    t = LANGUAGES.get(lang, LANGUAGES["en"])
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t["products"], callback_data="products"),
            InlineKeyboardButton(t["offers"], callback_data="offers"),
        ],
        [
            InlineKeyboardButton(t["account"], callback_data="account"),
            InlineKeyboardButton(t["orders"], callback_data="orders"),
        ],
        [InlineKeyboardButton(t["language"], callback_data="language")],
        [
            InlineKeyboardButton(t["telegram"], url=TELEGRAM_SUPPORT),
        ],
    ])

CHANNEL_USERNAME = "-1004372417917"
CHANNEL_URL = "https://t.me/bntechdigital02"


def channel_gate_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership")],
    ])



async def check_channel_membership(context, user_id):
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )
        if member.status in ("member", "administrator", "creator"):
            return True
        if member.status == "restricted":
            return bool(getattr(member, "is_member", False))
        return False
    except Exception:
        logger.exception("Channel membership check failed for user %s", user_id)
        return None


async def show_channel_gate(message):
    await message.reply_text(
        "?? Please join our Telegram channel before using this bot.\n\n"
        "1. Click Join Channel.\n"
        "2. After joining, click Verify Membership.",
        reply_markup=channel_gate_keyboard(),
    )

async def register_broadcast_subscriber(user):
    """Register a user who has started the bot for future broadcasts."""
    if not user:
        return
    payload = {
        "telegram_user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "is_active": True,
    }
    try:
        await asyncio.to_thread(
            supabase_mutate,
            "POST",
            "bntech_subscribers",
            payload,
            {"on_conflict": "telegram_user_id"},
        )
    except Exception as exc:
        response = getattr(exc, "response", None)
        if response is not None:
            logger.error(
                "Subscriber registration failed: HTTP %s; response: %s",
                response.status_code,
                response.text[:1000],
            )
        else:
            logger.exception("Could not register broadcast subscriber")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        logger.warning("/start received without effective_user")
        return

    logger.info("/start received for Telegram user ID %s", user.id)
    await register_broadcast_subscriber(user)
    logger.info("Subscriber registration function completed for user ID %s", user.id)

    # Require channel membership before showing the main menu.
    membership = await check_channel_membership(context, user.id)
    if membership is not True:
        await show_channel_gate(update.effective_message)
        return

    lang = user_language(context)
    t = LANGUAGES[lang]
    await update.effective_message.reply_text(
        f'{t["welcome"]}\n\n{t["intro"]}\n{t["prices"]}\n\n{t["choose"]}',
        reply_markup=main_menu(lang),
    )

# ---------------------------------------------------------------------------
# Supabase helpers (blocking; always called through asyncio.to_thread)
# ---------------------------------------------------------------------------
def parse_amount(value, currency_label):
    """Validate positive INR or USDT prices with correctly grouped commas."""
    import re

    if value is None:
        raise ValueError(f"{currency_label} price is required")

    currency = str(currency_label).strip().upper()
    raw = str(value).strip().upper()
    if not raw:
        raise ValueError(f"{currency} price is required")

    if currency == "INR":
        symbols = ("\u20b9", "\u00e2\u201a\u00b9")
        labels = ("INR",)
        max_decimals = 2
        max_value = 10_000_000
    elif currency == "USDT":
        symbols = ("$",)
        labels = ("USDT", "USD")
        max_decimals = 6
        max_value = float("inf")
    else:
        raise ValueError("Unsupported currency")

    # Strip at most one currency prefix or suffix.
    token = None
    for candidate in (*symbols, *labels):
        if raw.startswith(candidate):
            token = candidate
            raw = raw[len(candidate):].strip()
            break
    if token is None:
        for candidate in (*symbols, *labels):
            if raw.endswith(candidate):
                token = candidate
                raw = raw[:-len(candidate)].strip()
                break

    # Reject wrong-currency markers and any repeated/embedded labels.
    forbidden = ("$", "INR", "USDT", "USD")
    for marker in forbidden:
        if marker in raw:
            raise ValueError(f"Invalid currency format for {currency}")

    # ASCII digits only; reject Unicode digit lookalikes.
    if any(ch.isdigit() and not ch.isascii() for ch in raw):
        raise ValueError(f"Invalid numeric digits for {currency}")

    if not raw or not re.fullmatch(r"(?:\d[\d,]*(?:\.\d+)?|\.\d+)", raw):
        raise ValueError(f"{currency} price must be a valid positive number")

    if "," in raw:
        integer = raw.split(".", 1)[0]
        valid_grouping = (
            re.fullmatch(r"\d{1,3}(?:,\d{3})+", integer)
            or re.fullmatch(r"\d{1,2}(?:,\d{2})*,\d{3}", integer)
        )
        if not valid_grouping:
            raise ValueError("Invalid comma grouping in price")
        raw = raw.replace(",", "")

    decimal_part = raw.split(".", 1)[1] if "." in raw else ""
    if len(decimal_part) > max_decimals:
        raise ValueError(f"{currency} price has too many decimal places")

    amount = float(raw)
    if amount <= 0 or amount > max_value:
        raise ValueError(f"{currency} price is outside the allowed range")
    return amount

def supabase_get(table, params):
    """Generic GET on a Supabase REST table. Returns None if not configured."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def fetch_products():
    return supabase_get("bntech_products", {
        "select": "id,name,price_inr,price_usdt,stock,description",
        "is_active": "eq.true",
        "order": "name.asc",
    })


def fetch_offers():
    return supabase_get("bntech_offers", {
        "select": "title,description,discount_text,starts_at,ends_at",
        "is_active": "eq.true",
        "order": "created_at.desc",
    })


def fetch_my_orders(telegram_user_id):
    return supabase_get("bntech_orders", {
        "select": "id,product_id,quantity,total_inr,status,created_at",
        "telegram_user_id": f"eq.{telegram_user_id}",
        "order": "created_at.desc",
        "limit": "10",
    })


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------
async def show_products(query):
    try:
        products = await asyncio.to_thread(fetch_products)
    except requests.RequestException:
        logger.exception("Could not fetch products from Supabase")
        await query.message.reply_text(
            "Products are temporarily unavailable. Please try again later."
        )
        return

    if products is None:
        await query.message.reply_text(
            "Shop setup is incomplete. Please contact support."
        )
        return

    if not products:
        await query.message.reply_text("No products are available right now.")
        return

    await query.message.reply_text(
        "\U0001F6CD\uFE0F BN Tech Products\n\n"
        "Orders are confirmed only through WhatsApp. "
        "This message is not proof of payment."
    )

    user = query.from_user
    for product in products[:10]:
        name = str(product.get("name") or "Product")
        description = str(product.get("description") or "")
        text = (
            f"\U0001F4E6 {name}\n{description}\n"
            f"\U0001F4B0 Price: {product.get('price_inr', 'Contact us')}\n"
            f"\U0001F30D International price: {product.get('price_usdt', 'Contact us')} USDT\n"
            f"Stock: {product.get('stock', 'Contact us')}"
        )
        buttons, note = product_buy_buttons(user, product)
        if note:
            text += f"\n{note}"
        markup = InlineKeyboardMarkup(buttons) if buttons else None
        await query.message.reply_text(text, reply_markup=markup)


async def show_offers(query):
    try:
        offers = await asyncio.to_thread(fetch_offers)
    except requests.RequestException:
        logger.exception("Could not fetch BN Tech offers")
        await query.message.reply_text("Offers are temporarily unavailable. Please try again later.")
        return

    if offers is None:
        await query.message.reply_text("Offers setup is incomplete. Please contact support.")
        return

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    user = query.from_user
    await query.message.reply_text("BN Tech Offers")

    for offer in offers[:10]:
        title = str(offer.get("title") or "Special Offer")
        description = str(offer.get("description") or "")
        discount = str(offer.get("discount_text") or "")
        ends_at = offer.get("ends_at")
        expired = offer.get("is_active") is False

        if ends_at:
            try:
                expiry = datetime.fromisoformat(str(ends_at).replace("Z", "+00:00"))
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                expired = expired or expiry <= now
            except (ValueError, TypeError):
                expired = True

        text = f"{title}\n"
        if discount:
            text += f"{discount}\n"
        if description:
            text += description + "\n"

        if expired:
            await query.message.reply_text(text + "\nThis offer has expired.")
            continue

        text += "\nContact us on WhatsApp to confirm this offer."
        markup = None
        try:
            link = build_whatsapp_link(
                WHATSAPP_NUMBER,
                product="Offer",
                price=1,
                currency="INR",
                username=getattr(user, "username", None),
                telegram_id=getattr(user, "id", None),
                offer=title + (f" ({discount})" if discount else ""),
            )
            if is_valid_whatsapp_url(link):
                markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Contact on WhatsApp", url=link)]]
                )
        except (ValueError, TypeError):
            pass

        await query.message.reply_text(text, reply_markup=markup)

    if not offers:
        await query.message.reply_text("No offers are available right now.")


async def show_account(query, context=None):
    user = query.from_user
    username = f"@{user.username}" if user.username else "Not set"
    await query.message.reply_text(
        f'{tr(context, "account_title")}\n\n'
        f'{tr(context, "name")}: {user.full_name}\n'
        f'{tr(context, "username")}: {username}\n'
        f'{tr(context, "telegram_id")}: {user.id}\n\n'
        f'{tr(context, "orders_hint")}'
    )



def _invoice_text(value):
    """Escape untrusted database text before placing it in a PDF paragraph."""
    return escape(str(value if value is not None else "N/A"))


def _build_order_invoice(order, product):
    """Create a downloadable order invoice PDF in memory."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Order Invoice {order.get('id', '')}",
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("BN TECH ? ORDER INVOICE", styles["Title"]),
        Spacer(1, 8 * mm),
        Paragraph(f"Order ID: {_invoice_text(order.get('id'))}", styles["Normal"]),
        Paragraph(f"Order date: {_invoice_text(order.get('created_at'))}", styles["Normal"]),
        Paragraph(f"Payment status: {_invoice_text(order.get('status'))}", styles["Normal"]),
        Spacer(1, 7 * mm),
    ]

    product_name = (product or {}).get("name") or f"Product #{order.get('product_id', 'N/A')}"
    quantity = order.get("quantity", "N/A")
    total = order.get("total_inr")
    try:
        total_display = f"{float(total):,.2f}"
    except (TypeError, ValueError):
        total_display = f"{total if total is not None else 'N/A'}"

    rows = [
        ["Description", "Quantity", "Total (INR)"],
        [_invoice_text(product_name), _invoice_text(quantity), _invoice_text(total_display)],
    ]
    table = Table(rows, colWidths=[95 * mm, 30 * mm, 40 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([
        table,
        Spacer(1, 8 * mm),
        Paragraph(f"Order total: <b>{_invoice_text(total_display)}</b>", styles["Heading2"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "This document summarizes the order recorded by the bot. "
            "It is not a tax invoice or proof of payment.",
            styles["Italic"],
        ),
    ])
    doc.build(story)
    buffer.seek(0)
    return buffer


async def send_order_invoice(message, order_id, customer_id=None):
    """Fetch one order, enforce customer ownership when requested, then send its PDF."""
    try:
        orders = await asyncio.to_thread(supabase_get, "bntech_orders", {
            "select": "id,telegram_user_id,product_id,quantity,total_inr,status,created_at",
            "id": f"eq.{order_id}",
            "limit": "1",
        })
        if orders is None:
            await message.reply_text("Invoice service is not configured. Please contact support.")
            return
        if not orders:
            await message.reply_text("Order not found.")
            return

        order = orders[0]
        if customer_id is not None and str(order.get("telegram_user_id")) != str(customer_id):
            await message.reply_text("You can only download invoices for your own orders.")
            return

        products = await asyncio.to_thread(supabase_get, "bntech_products", {
            "select": "id,name",
            "id": f"eq.{order.get('product_id')}",
            "limit": "1",
        })
        product = products[0] if products else None
        pdf = _build_order_invoice(order, product)
        filename = f"invoice_{str(order.get('id', 'order')).replace('/', '_')}.pdf"
        await message.reply_document(
            document=pdf,
            filename=filename,
            caption=f"Order invoice #{order.get('id')}",
        )
    except requests.RequestException:
        logger.exception("Could not retrieve invoice order data")
        await message.reply_text("Could not load the order right now. Please try again later.")
    except Exception:
        logger.exception("Could not generate order invoice")
        await message.reply_text("Could not generate the PDF invoice. Please check the bot logs.")


async def show_orders(query, context=None):
    user = query.from_user
    try:
        orders = await asyncio.to_thread(fetch_my_orders, user.id)
    except requests.RequestException:
        logger.exception("Could not fetch BN Tech orders")
        await query.message.reply_text(tr(context, "load_error"))
        return

    if orders is None:
        await query.message.reply_text(tr(context, "setup_error"))
        return

    if not orders:
        await query.message.reply_text(
            f'{tr(context, "orders_title")}\n\n{tr(context, "no_orders")}'
        )
        return

    lines = [tr(context, "recent_orders") + "\n"]
    invoice_buttons = []
    for order in orders:
        order_id = order.get("id")
        lines.append(
            f'{tr(context, "order")} #{order_id or "N/A"}\n'
            f'{tr(context, "product_id")}: {order.get("product_id", "N/A")}\n'
            f'{tr(context, "quantity")}: {order.get("quantity", "N/A")}\n'
            f'{tr(context, "total")}: {order.get("total_inr", "N/A")}\n'
            f'{tr(context, "status")}: {order.get("status", "N/A")}\n'
            f'{tr(context, "date")}: {order.get("created_at") or "N/A"}\n'
        )
        if order_id is not None:
            invoice_buttons.append([
                InlineKeyboardButton(
                    f"Download Invoice #{order_id}",
                    callback_data=f"invoice_{encode_ref(order_id)}",
                )
            ])
    await query.message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(invoice_buttons) if invoice_buttons else None,
    )

async def show_language(query, context=None):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F1EC\U0001F1E7 English", callback_data="language_en")],
        [InlineKeyboardButton("\U0001F1EE\U0001F1F3 Hindi", callback_data="language_hi")],
        [InlineKeyboardButton("\U0001F1E7\U0001F1E9 Bangla", callback_data="language_bn")],
    ])
    await query.message.reply_text(tr(context, "language_title"), reply_markup=markup)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
HANDLERS = {
    "products": show_products,
    "offers": show_offers,
    "account": show_account,
    "orders": show_orders,
    "language": show_language,
}

def supabase_mutate(method, table, payload=None, params=None):
    """Perform a Supabase REST mutation using the service-role key."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase is not configured")
    response = requests.request(
        method,
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        json=payload,
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    if response.text.strip():
        return response.json()
    return []




def admin_mutate(user_id, method, table, payload=None, params=None):
    """Allow database mutations only for an authorized admin."""
    if not is_admin(user_id):
        raise PermissionError("Only an authorized admin can mutate data.")
    return supabase_mutate(method, table, payload, params)
def check_product_deletion_safety(pid):
    """Raise if a product cannot safely be deleted; database errors fail closed."""
    products = supabase_get("bntech_products", {
        "select": "id,name,stock",
        "id": f"eq.{pid}",
        "limit": "1",
    })
    if products is None:
        raise RuntimeError("Could not verify product data")
    if not products:
        raise ValueError("Product not found.")

    product = products[0]
    stock = product.get("stock")
    if isinstance(stock, bool):
        raise ValueError("Stock value is invalid; deletion blocked.")
    try:
        stock_number = int(stock)
        if str(stock).strip() != str(stock_number):
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("Stock value is invalid; deletion blocked.")

    if stock_number < 0:
        raise ValueError("Stock value is invalid; deletion blocked.")
    orders = supabase_get("bntech_orders", {
        "select": "id",
        "product_id": f"eq.{pid}",
        "limit": "1",
    })
    if orders is None:
        raise RuntimeError("Could not verify linked orders")
    if orders:
        raise ValueError("Not deleted: product is linked to existing orders.")

    return product



def product_view_keyboard(ref):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Edit", callback_data=f"admin_product_edit_{ref}")],
        [InlineKeyboardButton("Delete", callback_data=f"admin_product_delete_{ref}")],
        [InlineKeyboardButton("Products", callback_data="admin_products")],
    ])


def product_edit_keyboard(ref):
    buttons = []
    for field, code in PRODUCT_FIELD_KEYS.items():
        buttons.append([InlineKeyboardButton(
            field.replace("_", " ").title(),
            callback_data=f"admin_product_editfield_{ref}_{code}"
        )])
    buttons.append([InlineKeyboardButton("Back", callback_data=f"admin_product_view_{ref}")])
    return InlineKeyboardMarkup(buttons)


def product_delete_confirm_keyboard(ref):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Confirm delete", callback_data=f"admin_product_delete_confirm_{ref}"),
        InlineKeyboardButton("Cancel", callback_data=f"admin_product_view_{ref}"),
    ]])


def offer_view_keyboard(ref):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Delete", callback_data=f"admin_offer_delete_{ref}")],
        [InlineKeyboardButton("Offers", callback_data="admin_offers")],
    ])


def offer_delete_confirm_keyboard(ref):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Confirm delete", callback_data=f"admin_offer_delete_confirm_{ref}"),
        InlineKeyboardButton("Cancel", callback_data=f"admin_offer_view_{ref}"),
    ]])


def order_card(order):
    oid = encode_ref(order.get("id", ""))
    text = f"Order #{order.get('id', 'N/A')}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Pending", callback_data=f"admin_os_{oid}_P"),
         InlineKeyboardButton("Paid", callback_data=f"admin_os_{oid}_A"),
         InlineKeyboardButton("Cancel", callback_data=f"admin_os_{oid}_X")]
    ])
    return text, keyboard


def admin_products_keyboard(rows):
    buttons = [[InlineKeyboardButton("\u2795 Add product", callback_data="admin_product_add")]]
    for p in rows[:15]:
        pid = p.get("id")
        status = "??" if p.get("is_active", True) else "??"
        buttons.append([InlineKeyboardButton(
            f"{status} {str(p.get('name') or 'Product')[:35]} (ID {pid})",
            callback_data=f"admin_product_view_{encode_ref(pid)}",
        )])
    buttons.append([InlineKeyboardButton("🎁ï¸ Admin menu", callback_data="admin_home")])
    return InlineKeyboardMarkup(buttons)


def admin_offers_keyboard(rows):
    buttons = [[InlineKeyboardButton("\u2795 Add offer", callback_data="admin_offer_add")]]
    for o in rows[:15]:
        oid = o.get("id")
        status = "??" if o.get("is_active", True) else "??"
        buttons.append([InlineKeyboardButton(
            f"{status} {str(o.get('title') or 'Offer')[:35]} (ID {oid})",
            callback_data=f"admin_offer_view_{encode_ref(oid)}",
        )])
    buttons.append([InlineKeyboardButton("🎁ï¸ Admin menu", callback_data="admin_home")])
    return InlineKeyboardMarkup(buttons)


async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.from_user or not is_admin(query.from_user.id):
        await query.message.reply_text(
            "? Access Denied! You are not an admin."
        )
        return

    action = query.data
    if not action.startswith("admin_product_editfield_"):
        context.user_data.pop("admin_input", None)
    try:
        if action == "admin_home":
            context.user_data.pop("admin_input", None)
            await query.message.reply_text("\U0001F510 BN TECH ADMIN PANEL", reply_markup=admin_menu())

        elif action == "admin_stats":
            products, offers, orders = await asyncio.gather(
                asyncio.to_thread(supabase_get, "bntech_products", {"select": "id", "limit": "1000"}),
                asyncio.to_thread(supabase_get, "bntech_offers", {"select": "id", "is_active": "eq.true", "limit": "1000"}),
                asyncio.to_thread(supabase_get, "bntech_orders", {"select": "id,status,total_inr", "limit": "1000"}),
            )
            if products is None or offers is None or orders is None:
                raise RuntimeError("Supabase setup missing")
            pending = sum(str(o.get("status", "")).upper() in ("PENDING", "PAYMENT_PENDING") for o in orders)
            paid = sum(str(o.get("status", "")).upper() in ("PAID", "COMPLETED", "SUCCESS") for o in orders)
            revenue = sum(float(o.get("total_inr") or 0) for o in orders if str(o.get("status", "")).upper() in ("PAID", "COMPLETED", "SUCCESS"))
            await query.message.reply_text(
                "?? BN TECH STATISTICS\n\n"
                f"📦 Products: {len(products)}\n🎁 Active offers: {len(offers)}\n"
                f"?? Orders: {len(orders)}\n? Pending orders: {pending}\n"
                f"? Paid/completed orders: {paid}\n💰 Recorded paid revenue: {revenue:.2f}",
                reply_markup=admin_menu(),
            )

        elif action == "admin_products":
            rows = await asyncio.to_thread(supabase_get, "bntech_products", {
                "select": "id,name,price_inr,price_usdt,stock,is_active",
                "order": "id.desc", "limit": "100"
            })
            if rows is None:
                raise RuntimeError("Supabase setup missing")
            await query.message.reply_text(
                "📦 PRODUCT MANAGEMENT\nSelect a product or add one:",
                reply_markup=admin_products_keyboard(rows),
            )

        elif action.startswith("admin_product_view_"):
            pid = decode_ref(action[len("admin_product_view_"):])
            if pid is None:
                await query.message.reply_text("Invalid or expired product reference.")
                return
            rows = await asyncio.to_thread(supabase_get, "bntech_products", {
                "select": "id,name,description,price_inr,price_usdt,stock,is_active,warranty",
                "id": f"eq.{pid}", "limit": "1"
            })
            if not rows:
                await query.message.reply_text("Product not found.", reply_markup=admin_menu())
                return
            p = rows[0]
            active = bool(p.get("is_active", True))
            await query.message.reply_text(
                f"📦 {p.get('name')} (ID {pid})\nDescription: {p.get('description') or '-'}\n"
                f"INR: {p.get('price_inr')} | USDT: {p.get('price_usdt')}\n"
                f"Stock: {p.get('stock')} | Active: {active}\n"
                f"Warranty: {p.get('warranty') or 'Not set'}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("?? Edit", callback_data=f"admin_product_edit_{encode_ref(pid)}")],
                    [InlineKeyboardButton("?? Activate/Deactivate", callback_data=f"admin_product_toggle_{encode_ref(pid)}")],
                    [InlineKeyboardButton("??? Delete", callback_data=f"admin_product_delete_{encode_ref(pid)}")],
                    [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")],
                ]),
            )

        elif action == "admin_product_add":
            context.user_data["admin_input"] = {
                "kind": "product_add",
                "step": "name",
                "data": {},
            }
            await query.message.reply_text(
                "ADD PRODUCT ? Step 1 of 6\n\n"
                "Enter the product name.\n"
                "Send /cancel anytime to cancel."
            )

        elif action.startswith("admin_product_editfield_"):
            suffix = action[len("admin_product_editfield_"):]
            valid_fields = sorted(PRODUCT_EDIT_FIELDS, key=len, reverse=True)
            field_key = None
            ref = None
            for candidate in valid_fields:
                ending = "_" + candidate
                if suffix.endswith(ending):
                    ref = suffix[:-len(ending)]
                    field_key = candidate
                    break
            if field_key is None:
                ref, sep, code = suffix.rpartition("_")
                if sep:
                    field_key = code
            pid = decode_ref(ref) if ref else None
            field = PRODUCT_FIELD_CODES.get(field_key, field_key)
            if pid is None or field not in PRODUCT_EDIT_FIELDS:
                await query.message.reply_text("Unknown or stale product field.")
                return
            context.user_data["admin_input"] = {"kind": "product_edit", "id": str(pid), "field": field}
            prompts = {
                "name": "Send the new product name:",
                "description": "Send the new product description:",
                "price_inr": "Send the new INR price (examples: 99, INR 99, 99):",
                "price_usdt": "Send the new USDT price (examples: 1, USDT 1, $1):",
                "stock": "Send the new stock quantity (whole number, 0 or higher):",
                "is_active": "Send true to activate or false to deactivate this product:",
                            "warranty": "Send warranty details (up to 500 characters; blank clears it):",
            }
            await query.message.reply_text(f"?? Editing product ID {pid}\n{prompts[field]}\nSend /cancel to cancel.")

        elif action.startswith("admin_product_edit_"):
            pid = decode_ref(action[len("admin_product_edit_"):])
            if pid is None:
                await query.message.reply_text("Invalid or expired product reference.")
                return
            await query.message.reply_text(
                f"Choose which field to edit for product ID {pid}:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("?? Name", callback_data=f"admin_product_editfield_{encode_ref(pid)}_n"),
                     InlineKeyboardButton("?? Description", callback_data=f"admin_product_editfield_{encode_ref(pid)}_d")],
                    [InlineKeyboardButton("???? INR price", callback_data=f"admin_product_editfield_{encode_ref(pid)}_i"),
                     InlineKeyboardButton("?? USDT price", callback_data=f"admin_product_editfield_{encode_ref(pid)}_u")],
                    [InlineKeyboardButton("📦 Stock", callback_data=f"admin_product_editfield_{encode_ref(pid)}_s"),
                     InlineKeyboardButton("?? Active status", callback_data=f"admin_product_editfield_{encode_ref(pid)}_a")],
                     [InlineKeyboardButton("Warranty", callback_data=f"admin_product_editfield_{encode_ref(pid)}_w")],
                    [InlineKeyboardButton("🎁ï¸ Back to product", callback_data=f"admin_product_view_{encode_ref(pid)}")],
                ])
            )

        elif action.startswith("admin_product_toggle_"):
            pid = decode_ref(action[len("admin_product_toggle_"):])
            if pid is None:
                await query.message.reply_text("Invalid or expired product reference.")
                return
            rows = await asyncio.to_thread(supabase_get, "bntech_products", {
                "select": "is_active", "id": f"eq.{pid}", "limit": "1"
            })
            if not rows:
                raise RuntimeError("Product not found")
            new_active = not bool(rows[0].get("is_active", True))
            await asyncio.to_thread(admin_mutate, query.from_user.id, "PATCH", "bntech_products",
                                    {"is_active": new_active}, {"id": f"eq.{pid}"})
            await query.message.reply_text(f"Product {pid} active set to {new_active}.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
            ]))

        elif action.startswith("admin_product_delete_") and not action.startswith("admin_product_delete_confirm_"):
            pid = action.rsplit("_", 1)[1]
            try:
                product = await asyncio.to_thread(check_product_deletion_safety, pid)
            except ValueError as exc:
                buttons = [[InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]]
                if "linked to existing orders" in str(exc).lower():
                    buttons.insert(0, [InlineKeyboardButton("?? Toggle product status", callback_data=f"admin_product_toggle_{encode_ref(pid)}")])
                await query.message.reply_text(str(exc), reply_markup=InlineKeyboardMarkup(buttons))
                return
            except Exception:
                logger.exception("Could not verify product deletion safety")
                await query.message.reply_text(
                    "?? Could not verify stock/orders. Product was NOT deleted.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
                    ]),
                )
                return

            await query.message.reply_text(
                f"Delete product {product.get('name', pid)} (ID {pid})? This cannot be undone. "
                "Stock and linked orders will be checked again after confirmation.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("?? Confirm delete", callback_data=f"admin_product_delete_confirm_{pid}"),
                    InlineKeyboardButton("Cancel", callback_data=f"admin_product_view_{encode_ref(pid)}")
                ]]),
            )

        elif action.startswith("admin_product_delete_confirm_"):
            pid = decode_ref(action.rsplit("_", 1)[1])
            if pid is None:
                await query.message.reply_text("Invalid product reference.")
                return
            try:
                await asyncio.to_thread(check_product_deletion_safety, pid)
                deleted = await asyncio.to_thread(
                    admin_mutate, query.from_user.id, "DELETE", "bntech_products", None, {"id": f"eq.{pid}"}
                )
                if not deleted:
                    await query.message.reply_text(
                        "?? No product was deleted. It may have changed or already been removed.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
                        ]),
                    )
                    return
            except ValueError as exc:
                await query.message.reply_text(str(exc), reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
                ]))
                return
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                logger.exception("Product deletion rejected by database")
                message = (
                    "?? The database refused the delete. Product was not deleted."
                    if status_code == 409
                    else "?? Database error. Product was not reported as deleted."
                )
                await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
                ]))
                return
            except Exception:
                logger.exception("Could not safely delete product")
                await query.message.reply_text(
                    "?? Database request failed. Product was NOT deleted.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
                    ]),
                )
                return

            await query.message.reply_text(
                f"Product ID {pid} deleted.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁ï¸ Products", callback_data="admin_products")]
                ]),
            )

        elif action == "admin_offers":
            rows = await asyncio.to_thread(supabase_get, "bntech_offers", {
                "select": "id,title,description,discount_text,is_active,starts_at,ends_at",
                "order": "created_at.desc", "limit": "100"
            })
            if rows is None:
                raise RuntimeError("Supabase setup missing")
            await query.message.reply_text(
                "🎁 OFFER MANAGEMENT\nSelect an offer or add one:",
                reply_markup=admin_offers_keyboard(rows),
            )

        elif action.startswith("admin_offer_view_"):
            oid = action.rsplit("_", 1)[1]
            rows = await asyncio.to_thread(supabase_get, "bntech_offers", {
                "select": "id,title,description,discount_text,is_active,starts_at,ends_at",
                "id": f"eq.{oid}", "limit": "1"
            })
            if not rows:
                await query.message.reply_text("Offer not found.", reply_markup=admin_menu())
                return
            o = rows[0]
            await query.message.reply_text(
                f"🎁 {o.get('title')} (ID {oid})\n{ o.get('description') or '' }\n"
                f"Discount: {o.get('discount_text') or '-'}\nActive: {o.get('is_active')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("?? Edit", callback_data=f"admin_offer_edit_{oid}")],
                    [InlineKeyboardButton("?? Activate/Deactivate", callback_data=f"admin_offer_toggle_{oid}")],
                    [InlineKeyboardButton("??? Delete", callback_data=f"admin_offer_delete_{oid}")],
                    [InlineKeyboardButton("🎁ï¸ Offers", callback_data="admin_offers")],
                ]),
            )

        elif action == "admin_offer_add":
            context.user_data["admin_input"] = {"kind": "offer_add"}
            await query.message.reply_text(
                "Send offer details in ONE message:\ntitle | description | discount text\n"
                "Example: Launch Offer | Contact support to order | 10% off\n"
                "Send /cancel to cancel."
            )

        elif action.startswith("admin_offer_edit_"):
            oid = action.rsplit("_", 1)[1]
            context.user_data["admin_input"] = {"kind": "offer_edit", "id": oid}
            await query.message.reply_text(
                f"Send field to change for offer ID {oid}: title=value OR description=value OR discount_text=value OR is_active=true/false\n"
                "Send /cancel to cancel."
            )

        elif action.startswith("admin_offer_toggle_"):
            oid = action.rsplit("_", 1)[1]
            rows = await asyncio.to_thread(supabase_get, "bntech_offers", {
                "select": "is_active", "id": f"eq.{oid}", "limit": "1"
            })
            if not rows:
                raise RuntimeError("Offer not found")
            new_active = not bool(rows[0].get("is_active", True))
            await asyncio.to_thread(admin_mutate, query.from_user.id, "PATCH", "bntech_offers",
                                    {"is_active": new_active}, {"id": f"eq.{oid}"})
            await query.message.reply_text(f"Offer {oid} active set to {new_active}.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁ï¸ Offers", callback_data="admin_offers")]
            ]))

        elif action.startswith("admin_offer_delete_") and not action.startswith("admin_offer_delete_confirm_"):
            oid = action.rsplit("_", 1)[1]
            await query.message.reply_text(
                f"Delete offer ID {oid}? This cannot be undone.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("?? Confirm delete", callback_data=f"admin_offer_delete_confirm_{oid}"),
                    InlineKeyboardButton("Cancel", callback_data=f"admin_offer_view_{encode_ref(oid)}")
                ]]),
            )

        elif action.startswith("admin_offer_delete_confirm_"):
            oid = action.rsplit("_", 1)[1]
            await asyncio.to_thread(admin_mutate, query.from_user.id, "DELETE", "bntech_offers", None, {"id": f"eq.{oid}"})
            await query.message.reply_text(f"Offer ID {oid} deleted.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁ï¸ Offers", callback_data="admin_offers")]
            ]))

        elif action == "admin_customers":
            orders, tickets = await asyncio.gather(
                asyncio.to_thread(supabase_get, "bntech_orders", {
                    "select": "telegram_user_id,username,created_at",
                    "order": "created_at.desc", "limit": "1000"
                }),
                asyncio.to_thread(supabase_get, "bntech_support_tickets", {
                    "select": "telegram_user_id,username,first_name,created_at",
                    "order": "created_at.desc", "limit": "1000"
                }),
            )

            if orders is None or tickets is None:
                raise RuntimeError("Could not load customer records from Supabase")

            customers = {}

            for row in orders + tickets:
                customer_id = row.get("telegram_user_id")
                if customer_id is None:
                    continue

                key = str(customer_id)
                if key not in customers:
                    customers[key] = {
                        "telegram_user_id": customer_id,
                        "username": row.get("username"),
                        "first_name": row.get("first_name"),
                        "created_at": row.get("created_at"),
                    }
                else:
                    customer = customers[key]
                    if not customer.get("username") and row.get("username"):
                        customer["username"] = row["username"]
                    if not customer.get("first_name") and row.get("first_name"):
                        customer["first_name"] = row["first_name"]
                    if row.get("created_at") and (
                        not customer.get("created_at")
                        or row["created_at"] > customer["created_at"]
                    ):
                        customer["created_at"] = row["created_at"]

            recent = sorted(
                customers.values(),
                key=lambda c: c.get("created_at") or "",
                reverse=True,
            )[:50]

            if not recent:
                await query.message.reply_text(
                    "No customer records found in orders or support tickets.",
                    reply_markup=admin_menu(),
                )
            else:
                lines = [f"RECENT CUSTOMERS ({len(recent)})"]
                for c in recent:
                    username = (
                        "@" + c["username"]
                        if c.get("username")
                        else "No username recorded"
                    )
                    lines.append(
                        f"ID: {c['telegram_user_id']}\n"
                        f"Name: {c.get('first_name') or 'N/A'} | {username}\n"
                        f"Last record: {c.get('created_at') or 'N/A'}"
                    )

                await query.message.reply_text(
                    "\n\n".join(lines),
                    reply_markup=admin_menu(),
                )

        elif action == "admin_support":
            rows = await asyncio.to_thread(supabase_get, "bntech_support_tickets", {
                "select": "*", "limit": "20"
            })
            if rows is None:
                raise RuntimeError("Supabase setup missing")
            if not rows:
                await query.message.reply_text("?? No support tickets found.", reply_markup=admin_menu())
            else:
                # Display ticket fields dynamically because the project's ticket schema can vary.
                lines = ["?? RECENT SUPPORT TICKETS"]
                for ticket in rows[:10]:
                    safe_fields = []
                    for key, value in ticket.items():
                        if key.lower() in {"id", "telegram_user_id", "customer_id", "status", "subject", "message", "created_at"}:
                            safe_fields.append(f"{key}: {str(value)[:250]}")
                    lines.append("\n".join(safe_fields) if safe_fields else str(ticket)[:500])
                await query.message.reply_text("\n\n".join(lines), reply_markup=admin_menu())

        elif action.startswith("admin_inv_"):
            ref = action.removeprefix("admin_inv_")
            order_id = decode_ref(ref)
            if order_id is None:
                await query.message.reply_text("Invalid or expired order reference.")
                return
            await send_order_invoice(query.message, order_id)

        elif action == "admin_orders":
            rows = await asyncio.to_thread(supabase_get, "bntech_orders", {
                "select": "id,telegram_user_id,product_id,quantity,total_inr,status,created_at",
                "order": "created_at.desc", "limit": "20"
            })
            if rows is None:
                raise RuntimeError("Supabase setup missing")
            if not rows:
                await query.message.reply_text("No orders found.", reply_markup=admin_menu())
            else:
                for o in rows:
                    oid = encode_ref(o.get("id"))
                    buttons = [
                        [InlineKeyboardButton("Download / Resend Invoice", callback_data=f"admin_inv_{oid}")],
                        [InlineKeyboardButton("? Pending", callback_data=f"admin_os_{oid}_P"),
                         InlineKeyboardButton("? Paid", callback_data=f"admin_os_{oid}_A")],
                        [InlineKeyboardButton("? Cancel", callback_data=f"admin_os_{oid}_X")],
                    ]
                    await query.message.reply_text(
                        f"?? Order #{o.get('id')}\\nCustomer: {o.get('telegram_user_id')}\\n"
                        f"Product ID: {o.get('product_id')} | Qty: {o.get('quantity')}\\n"
                        f"Total: {o.get('total_inr')}\\nStatus: {o.get('status')}\\n"
                        f"Date: {o.get('created_at') or 'N/A'}\\n"
                        "Status buttons are requests, not proof of payment.",
                        reply_markup=InlineKeyboardMarkup(buttons),
                    )
                await query.message.reply_text("?? Admin menu", reply_markup=admin_menu())

        elif action.startswith("admin_os_"):
            parsed = parse_order_status_callback(action)
            if not parsed:
                await query.message.reply_text("This status request is outdated or invalid.")
                return
            order_id, new_status = parsed
            rows = await asyncio.to_thread(supabase_get, "bntech_orders", {
                "select": "id,status,telegram_user_id,product_id,quantity,total_inr,created_at",
                "id": f"eq.{order_id}", "limit": "1"
            })
            if rows is None:
                raise RuntimeError("Supabase setup missing")
            if not rows:
                await query.message.reply_text("Order not found.")
                return
            order = rows[0]
            old_status = order.get("status")
            allowed, reason = check_transition(old_status, new_status)
            if not allowed:
                await query.message.reply_text(reason)
                return
            token = store_pending_status(context, order_id, old_status, new_status)
            if not token:
                await query.message.reply_text("Could not create confirmation. Please try again.")
                return
            confirm_text = (
                f"Confirm order #{order_id} status change?\\n"
                f"Current: {old_status or 'NULL'}\\nNew: {new_status}\\n"
                f"{reason}\\n\\nNo customer notification will be sent."
            )
            await query.message.reply_text(
                confirm_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Confirm status change", callback_data=f"admin_oc_{token}"),
                    InlineKeyboardButton("Cancel", callback_data="admin_orders"),
                ]]),
            )

        elif action.startswith("admin_oc_"):
            token = action[len("admin_oc_"):]
            pending = get_pending_status(context, token, consume=True)
            if not pending or not all(k in pending for k in ("order_id", "old_status", "new_status")):
                await query.message.reply_text("Confirmation expired or was already used.")
                return
            order_id = pending["order_id"]
            old_status = pending["old_status"]
            new_status = pending["new_status"]

            rows = await asyncio.to_thread(supabase_get, "bntech_orders", {
                "select": "id,status,telegram_user_id,product_id,quantity,total_inr,created_at",
                "id": f"eq.{order_id}", "limit": "1"
            })
            if rows is None:
                raise RuntimeError("Supabase setup missing")
            if not rows:
                await query.message.reply_text("Order not found; no changes made.")
                return
            current = rows[0]
            if current.get("status") != old_status:
                await query.message.reply_text(
                    f"Order status changed while you were reviewing it; current status is {current.get('status')}. No update made."
                )
                current_ref = encode_ref(current.get("id"))
                await query.message.reply_text(
                    f"Order #{order_id}\\nStatus: {current.get('status')}\\n"
                    f"Total: {current.get('total_inr')}\\n"
                    "Status buttons are requests, not proof of payment.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("? Pending", callback_data=f"admin_os_{current_ref}_P"),
                         InlineKeyboardButton("? Paid", callback_data=f"admin_os_{current_ref}_A")],
                        [InlineKeyboardButton("? Cancel", callback_data=f"admin_os_{current_ref}_X")],
                        [InlineKeyboardButton("🎁ï¸ Orders", callback_data="admin_orders")],
                    ]),
                )
                return

            result = await asyncio.to_thread(
                admin_mutate, query.from_user.id, "PATCH", "bntech_orders",
                {"status": new_status},
                {"id": f"eq.{order_id}", "status": status_match_filter(old_status)}
            )
            if not result:
                await query.message.reply_text("No order was updated. Reload orders and try again.")
                return
            await query.message.reply_text(
                f"Order #{order_id} status updated to {new_status}. Customer has not been notified.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎁ï¸ Orders", callback_data="admin_orders")
                ]]),
            )

    except requests.RequestException as exc:
        logger.exception("Admin database request failed")
        await query.message.reply_text(
            "?? Database request failed. Check Supabase permissions/schema and try again."
        )
    except Exception:
        logger.exception("Admin action failed: %s", action)
        await query.message.reply_text("?? Admin action failed. Check CMD logs for details.")


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not user or not is_admin(user.id):
        return
    state = context.user_data.get("admin_input")
    if not state:
        return
    text = (update.effective_message.text or "").strip()
    if text.lower() == "/cancel":
        context.user_data.pop("admin_input", None)
        await update.effective_message.reply_text("Cancelled.", reply_markup=admin_menu())
        return

    kind = state.get("kind")
    try:
        if kind == "product_add":
            step = state.get("step", "name")
            data = state.setdefault("data", {})

            if step == "name":
                if not text:
                    raise ValueError("Product name cannot be empty.")
                if len(text) > 100:
                    raise ValueError("Product name must be 100 characters or fewer.")
                data["name"] = text
                state["step"] = "description"
                await update.effective_message.reply_text(
                    "Step 2 of 6 ? Description\n\nEnter the product description."
                )

            elif step == "description":
                if not text:
                    raise ValueError("Description cannot be empty.")
                data["description"] = text
                state["step"] = "price_inr"
                await update.effective_message.reply_text(
                    "Step 3 of 6 ? INR price\n\nEnter the price in INR, for example: 199"
                )

            elif step == "price_inr":
                amount = parse_amount(text, "INR")
                if amount < 0:
                    raise ValueError("INR price cannot be negative.")
                data["price_inr"] = amount
                state["step"] = "price_usdt"
                await update.effective_message.reply_text(
                    "Step 4 of 6 ? USDT price\n\nEnter the price in USDT, for example: 2.5"
                )

            elif step == "price_usdt":
                amount = parse_amount(text, "USDT")
                if amount < 0:
                    raise ValueError("USDT price cannot be negative.")
                data["price_usdt"] = amount
                state["step"] = "stock"
                await update.effective_message.reply_text(
                    "Step 5 of 6 ? Stock quantity\n\nEnter a whole number, for example: 10"
                )

            elif step == "stock":
                try:
                    stock = int(text)
                except ValueError:
                    raise ValueError("Stock must be a whole number, for example: 10.")
                if stock < 0:
                    raise ValueError("Stock cannot be negative.")
                data["stock"] = stock
                state["step"] = "warranty"
                await update.effective_message.reply_text(
                    "Step 6 of 6 ? Warranty\n\n"
                    "Enter warranty text, e.g. 3 months or lifetime.\n"
                    "Send /skip if there is no warranty."
                )

            elif step == "warranty":
                warranty = "" if text.lower() == "/skip" else text
                if len(warranty) > 500:
                    raise ValueError("Warranty must be 500 characters or fewer.")
                data["warranty"] = warranty
                state["step"] = "confirm"
                warranty_display = warranty or "Not set"
                await update.effective_message.reply_text(
                    "Please confirm this product:\n\n"
                    f"Name: {data['name']}\n"
                    f"Description: {data['description']}\n"
                    f"INR price: {data['price_inr']}\n"
                    f"USDT price: {data['price_usdt']}\n"
                    f"Stock: {data['stock']}\n"
                    f"Warranty: {warranty_display}\n\n"
                    "Reply YES to save, or /cancel to cancel."
                )

            elif step == "confirm":
                if text.lower() not in {"yes", "confirm"}:
                    raise ValueError("Reply YES to save the product, or send /cancel.")
                payload = {
                    "name": data["name"],
                    "description": data["description"],
                    "price_inr": data["price_inr"],
                    "price_usdt": data["price_usdt"],
                    "stock": data["stock"],
                    "warranty": data.get("warranty", ""),
                    "is_active": True,
                }
                await asyncio.to_thread(
                    admin_mutate, user.id, "POST", "bntech_products", payload
                )
                context.user_data.pop("admin_input", None)
                await update.effective_message.reply_text(
                    "Product added successfully.", reply_markup=admin_menu()
                )

            else:
                context.user_data.pop("admin_input", None)
                raise ValueError("Product form state was invalid. Please start again.")

        elif kind == "product_edit":
            # Confirm the product still exists before accepting an edit.
            product_id = decode_ref(str(state.get("id", "")))
            if product_id is None:
                raise ValueError("Product not found.")
            exists = await asyncio.to_thread(supabase_get, "bntech_products", {
                "select": "id", "id": f"eq.{product_id}", "limit": "1"
            })
            if not exists:
                context.user_data.pop("admin_input", None)
                await update.effective_message.reply_text("Product not found.")
                return
            # New button-based flow stores the field in state; legacy field=value still works.
            if state.get("field"):
                field, value = state["field"], text.strip()
            else:
                if "=" not in text:
                    raise ValueError("Choose a field from the edit buttons, then send its new value")
                field, value = [x.strip() for x in text.split("=", 1)]
            allowed = {"name", "description", "price_inr", "price_usdt", "stock", "is_active", "warranty"}
            if field not in allowed:
                raise ValueError("Unknown field")
            if field in {"name", "description"} and not value.strip():
                raise ValueError("This field cannot be empty")
            if field == "name" and any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
                raise ValueError("Product name must not contain control characters or line breaks")
            if field == "description" and any(
                (ord(ch) < 32 and ch not in ("\n", "\r", "\t")) or ord(ch) == 127
                for ch in value
            ):
                raise ValueError("Description contains unsupported control characters")
            if field == "name" and len(value) > 100:
                raise ValueError("Product name must be 100 characters or fewer")
            if field == "description" and len(value) > 1000:
                raise ValueError("Product description must be 1000 characters or fewer")
            if field == "warranty":
                if len(value) > 500:
                    raise ValueError("Warranty must be 500 characters or fewer")
                if any((ord(ch) < 32 and ch not in ("\n", "\r", "\t")) or ord(ch) == 127 for ch in value):
                    raise ValueError("Warranty contains unsupported control characters")
            if field == "price_inr":
                value = parse_amount(value, "INR")
            elif field == "price_usdt":
                value = parse_amount(value, "USDT")
            elif field == "stock":
                if not value.isascii() or not value.isdigit():
                    raise ValueError("Stock must be a whole number")
                value = int(value)
                if value < 0 or value >= 99999999:
                    raise ValueError("Stock must be between 0 and 99999998")
            elif field == "is_active":
                if value.lower() not in {"true", "false"}: raise ValueError("Use true or false")
                value = value.lower() == "true"
            await asyncio.to_thread(admin_mutate, user.id, "PATCH", "bntech_products",
                                    {field: value}, {"id": f"eq.{state['id']}"})
            context.user_data.pop("admin_input", None)
            await update.effective_message.reply_text(
                f"? Product ID {state['id']} updated successfully.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📦 View products", callback_data="admin_products")],
                    [InlineKeyboardButton("?? Admin menu", callback_data="admin_home")],
                ])
            )

        elif kind == "offer_add":
            parts = [x.strip() for x in text.split("|")]
            if len(parts) != 3:
                raise ValueError("Use exactly 3 fields separated by |")
            title, description, discount_text = parts
            if not title or not description or not discount_text:
                raise ValueError("Offer title, description, and discount cannot be empty")
            if len(discount_text) > 100:
                raise ValueError("Offer discount text must be 100 characters or fewer")
            payload = {"title": title, "description": description,
                       "discount_text": discount_text, "is_active": True}
            await asyncio.to_thread(admin_mutate, user.id, "POST", "bntech_offers", payload)
            context.user_data.pop("admin_input", None)
            await update.effective_message.reply_text("? Offer added.", reply_markup=admin_menu())

        elif kind == "offer_edit":
            if "=" not in text:
                raise ValueError("Use field=value")
            field, value = [x.strip() for x in text.split("=", 1)]
            allowed = {"title", "description", "discount_text", "is_active"}
            if field not in allowed:
                raise ValueError("Unknown field")
            if field in {"title", "description", "discount_text"} and not value:
                raise ValueError("This field cannot be empty")
            if field == "discount_text" and len(value) > 100:
                raise ValueError("Offer discount text must be 100 characters or fewer")
            if field == "title" and len(value) > 100:
                raise ValueError("Offer title must be 100 characters or fewer")
            if field == "is_active":
                if value.lower() not in {"true", "false"}: raise ValueError("Use true or false")
                value = value.lower() == "true"
            await asyncio.to_thread(admin_mutate, user.id, "PATCH", "bntech_offers",
                                    {field: value}, {"id": f"eq.{state['id']}"})
            context.user_data.pop("admin_input", None)
            await update.effective_message.reply_text("? Offer updated.", reply_markup=admin_menu())
    except ValueError as exc:
        await update.effective_message.reply_text(
            f"?? {exc}\nPlease try again, or send /cancel."
        )
    except Exception:
        logger.exception("Admin text action failed")
        await update.effective_message.reply_text(
            "?? Could not save this change. Check CMD logs and Supabase schema/permissions."
        )


async def cancel_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.effective_message.reply_text("? Access Denied! You are not an admin.")
        return
    context.user_data.pop("admin_input", None)
    await update.effective_message.reply_text("Admin input cancelled.", reply_markup=admin_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    # Verify button is handled before the customer-access gate.
    if data == "verify_membership":
        user = query.from_user
        if is_admin(user.id):
            lang = user_language(context)
            t = LANGUAGES[lang]
            await query.message.reply_text(
                f'{t["welcome"]}\n\n{t["intro"]}\n{t["prices"]}\n\n{t["choose"]}',
                reply_markup=main_menu(lang),
            )
            return

        membership = await check_channel_membership(context, user.id)
        if membership is True:
            lang = user_language(context)
            t = LANGUAGES[lang]
            await query.message.reply_text(
                f'{t["welcome"]}\n\n{t["intro"]}\n{t["prices"]}\n\n{t["choose"]}',
                reply_markup=main_menu(lang),
            )
        elif membership is False:
            await query.message.reply_text(
                "?? You are not showing as a channel member yet. "
                "Please join the channel, then tap Verify Membership again.",
                reply_markup=channel_gate_keyboard(),
            )
        else:
            await query.message.reply_text(
                "?? We could not verify your membership right now. "
                "Please try again shortly.",
                reply_markup=channel_gate_keyboard(),
            )
        return

    # Keep admin callback handling separate; only gate regular customer buttons.
    if not is_admin(query.from_user.id):
        membership = await check_channel_membership(context, query.from_user.id)
        if membership is not True:
            await query.message.reply_text(
                "?? Please join our Telegram channel and verify your membership "
                "before using this bot.",
                reply_markup=channel_gate_keyboard(),
            )
            return

    if data.startswith("language_"):
        lang = data.removeprefix("language_")
        if lang not in LANGUAGES:
            logger.warning("Unknown language callback: %s", data)
            return
        context.user_data["language"] = lang
        await query.message.reply_text(
            tr(context, "language_saved"),
            reply_markup=main_menu(lang),
        )
        return

    if data.startswith("invoice_"):
        ref = data.removeprefix("invoice_")
        order_id = decode_ref(ref)
        if order_id is None:
            await query.message.reply_text("Invalid or expired order reference.")
            return
        await send_order_invoice(query.message, order_id, customer_id=query.from_user.id)
        return

    handler = HANDLERS.get(data)
    if handler is None:
        logger.warning("Unknown callback_data: %s", data)
        return

    if data in ("account", "orders", "language"):
        await handler(query, context)
    else:
        await handler(query)



# Admin-only broadcast. Initial recipient source: customers in orders/support tickets.
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if not user or not is_admin(user.id):
        if message:
            await message.reply_text("Access denied.")
        return

    context.user_data.pop("broadcast_source", None)
    context.user_data["broadcast_waiting_for_content"] = True
    await message.reply_text(
        "?? Broadcast draft mode\n\n"
        "Ab text message ya photo/offer poster caption ke saath bhejo.\n"
        "Uske baad bot confirmation dikhayega. Abhi kisi ko message nahi jayega.\n"
        "Cancel karne ke liye /cancel bhejo."
    )


async def broadcast_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    if not user or not is_admin(user.id):
        return
    if not context.user_data.get("broadcast_waiting_for_content") or not message:
        return

    if not (message.text and not message.text.startswith("/")) and not message.photo:
        await message.reply_text("Text message ya photo/poster bhejo. Cancel: /cancel")
        return

    context.user_data["broadcast_waiting_for_content"] = False
    context.user_data["broadcast_source"] = {
        "chat_id": message.chat_id,
        "message_id": message.message_id,
    }
    await message.reply_text(
        "Preview draft ready. Ye content available customer IDs ko bheja jayega.\n"
        "Recipients: unique IDs found in orders + support tickets.\n"
        "Order/support ticket na banane wale users is list mein nahi honge.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("? Confirm broadcast", callback_data="broadcast_confirm"),
            InlineKeyboardButton("? Cancel", callback_data="broadcast_cancel"),
        ]]),
    )


async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user if query else None
    if not query or not user or not is_admin(user.id):
        if query:
            await query.answer("Access denied.", show_alert=True)
        return

    await query.answer()
    action = query.data

    if action == "broadcast_cancel":
        context.user_data.pop("broadcast_source", None)
        context.user_data.pop("broadcast_waiting_for_content", None)
        await query.edit_message_text("Broadcast cancelled. Nothing was sent.")
        return

    source = context.user_data.get("broadcast_source")
    if not source:
        await query.edit_message_text("No pending broadcast draft. Use /broadcast again.")
        return

    # Consume the draft before sending to prevent accidental duplicate confirmations.
    context.user_data.pop("broadcast_source", None)

    try:
        subscribers = await asyncio.to_thread(
            supabase_get,
            "bntech_subscribers",
            {
                "select": "telegram_user_id",
                "is_active": "eq.true",
                "order": "created_at.asc",
                "limit": "10000",
            },
        )
        if subscribers is None:
            raise RuntimeError("Could not read bntech_subscribers from Supabase.")

        recipients = set()
        for row in subscribers:
            raw_id = row.get("telegram_user_id")
            if raw_id is None:
                continue
            try:
                recipient_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if recipient_id not in ADMIN_IDS:
                recipients.add(recipient_id)

    except Exception:
        logger.exception("Broadcast recipient lookup failed")
        await query.edit_message_text(
            "Broadcast not sent: recipient lookup failed. Check Supabase and try again."
        )
        return

    if not recipients:
        await query.edit_message_text(
            "Broadcast not sent: no active subscribers found in bntech_subscribers. Users must start the bot first."
        )
        return

    await query.edit_message_text(
        f"Broadcast started: channel + {len(recipients)} customer IDs..."
    )

    # Publish the same message to the configured public channel.
    channel_sent = False
    channel_error = ""
    try:
        await context.bot.copy_message(
            chat_id="@bntechdigital02",
            from_chat_id=source["chat_id"],
            message_id=source["message_id"],
        )
        channel_sent = True
        logger.info("Broadcast successfully posted to @bntechdigital02.")
    except Exception as exc:
        channel_error = f"{type(exc).__name__}: {str(exc)[:250]}"
        logger.warning("Channel broadcast failed: %s", channel_error)

    # Continue private delivery even if channel posting fails.
    sent = 0
    failed = 0
    for recipient_id in sorted(recipients):
        try:
            await context.bot.copy_message(
                chat_id=recipient_id,
                from_chat_id=source["chat_id"],
                message_id=source["message_id"],
            )
            sent += 1
        except Exception as exc:
            failed += 1
            logger.warning(
                "Broadcast delivery failed for recipient ID %s: %s: %s",
                recipient_id,
                type(exc).__name__,
                str(exc)[:500],
            )

            # Deactivate subscribers who have blocked the bot.
            try:
                from telegram.error import Forbidden

                if isinstance(exc, Forbidden) and "blocked by the user" in str(exc).lower():
                    await asyncio.to_thread(
                        supabase_mutate,
                        "PATCH",
                        "bntech_subscribers",
                        {"is_active": False},
                        {"telegram_user_id": f"eq.{recipient_id}"},
                    )
                    logger.info(
                        "Marked blocked subscriber %s as inactive.",
                        recipient_id,
                    )
            except Exception:
                logger.exception(
                    "Could not deactivate blocked subscriber %s.",
                    recipient_id,
                )

    channel_status = "SUCCESS" if channel_sent else "FAILED"
    report = (
        f"Broadcast finished\n"
        f"Channel (@bntechdigital02): {channel_status}\n"
        f"Active customer recipients: {len(recipients)}\n"
        f"Private messages sent: {sent}\n"
        f"Private messages failed: {failed}"
    )
    if channel_error:
        report += f"\nChannel error: {channel_error}"

    await query.message.reply_text(report)


async def set_broadcast_command_menu(application):
    from telegram import BotCommand, BotCommandScopeChat

    for admin_id in ADMIN_IDS:
        await application.bot.set_my_commands(
            [
                BotCommand("start", "Start the bot"),
                BotCommand("admin", "Open admin panel"),
                BotCommand("broadcast", "Send a broadcast"),
                BotCommand("cancel", "Cancel current action"),
            ],
            scope=BotCommandScopeChat(chat_id=admin_id),
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env file mein missing hai.")

    if not WHATSAPP_NUMBER or not normalize_whatsapp_number(WHATSAPP_NUMBER):
        raise RuntimeError("WHATSAPP_NUMBER .env file mein missing ya invalid hai.")

    app = Application.builder().token(BOT_TOKEN).post_init(set_broadcast_command_menu).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(broadcast_callback, pattern=r"^broadcast_(confirm|cancel)$"))
    app.add_handler(
        CallbackQueryHandler(admin_button_handler, pattern=r"^admin_")
    )
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.PHOTO | (filters.TEXT & ~filters.COMMAND)), broadcast_content_handler), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler), group=1)

    app.add_handler(CommandHandler("cancel", cancel_admin_input))

    logger.info("BN Tech Bot is starting...")
    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling()

# Temporary helper integration from patch_bot.py
from patch_bot import (
    get_pending_status,
    product_buy_buttons,
    PRODUCT_FIELD_KEYS,
    PRODUCT_FIELD_CODES,
    PRODUCT_EDIT_FIELDS,
    WHATSAPP_NUMBER,
    WA_MAX_URL_CHARS,
    WA_MAX_TEXT_CHARS,
    MAX_PENDING_CONFIRMATIONS,
    PENDING_CONFIRM_TTL,
    ORDER_STATUSES,
    _UUID_RE,
    _REF_CACHE,
    _REF_CACHE_LIMIT,
    normalize_whatsapp_number,
    build_whatsapp_link,
    is_valid_whatsapp_url,
    encode_ref,
    decode_ref,
    parse_order_status_callback,
    status_match_filter,
    check_transition,
    store_pending_status,
)

if __name__ == "__main__":
    main()
