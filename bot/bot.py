# bot.py
import os
import json
import uuid
import datetime
from urllib.parse import quote, urlparse
import io

import aiohttp
from aiohttp import web
import discord
from discord.ext import commands

# ================================================================
# グローバルセッション
# ================================================================
session: aiohttp.ClientSession = None

# ================================================================
# BOT設定（環境変数推奨）
# ================================================================
BOT_TOKEN = "トークンを入れてください"
CLIENT_ID = "IDを入れてください"
CLIENT_SECRET = "シークレットを入れてください"

# 適時変更
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
PORT = int(os.getenv("PORT", 8080))

if any(val.startswith("YOUR") for val in [BOT_TOKEN, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("BOT_TOKEN, CLIENT_ID, CLIENT_SECRET のいずれかが未設定です。")
if BASE_URL == "http://localhost:8080":
    print("⚠️ 警告: BASE_URL がローカルのままです。このままでは使用できないため、公開URLを指定してください。")

# ================================================================
# データストア
# ================================================================
DB_FILE = "verification_db.json"
try:
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
except FileNotFoundError:
    db = {"panels": {}, "states": {}}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

# ================================================================
# スコープ情報
# ================================================================
SCOPE_DESCRIPTIONS = {
    "identify": {"name": "ユーザー情報", "desc": "ユーザー名・アバター・IDなどにアクセスします。"},
    "email": {"name": "メールアドレス", "desc": "登録メールアドレスにアクセスします。"},
    "connections": {"name": "外部連携", "desc": "連携している外部サービス情報にアクセスします。"},
    "guilds": {"name": "参加サーバー", "desc": "ユーザーが所属しているサーバー一覧にアクセスします。"},
    "guilds.join": {"name": "サーバー参加", "desc": "ユーザーをサーバーに追加できます。"},
    "guilds.members.read": {"name": "メンバー情報", "desc": "サーバー内のプロフィールを読み取ります。"},
}

# ================================================================
# HTMLテンプレート
# ================================================================
def get_html_template(title, body_html, theme_color="#5865F2"):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');

/* ベース */
body {{
    font-family: 'Noto Sans JP', sans-serif;
    background: linear-gradient(135deg, #2C2F33, #1F2124);
    color: #F2F3F5;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
}}

/* カード */
.card {{
    background: #2B2D31;
    border-radius: 16px;
    box-shadow: 0 12px 24px rgba(0,0,0,0.4);
    width: 90%;
    max-width: 500px;
    padding: 40px 32px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.5);
}}

/* アイコン */
.icon {{
    font-size: 64px;
    margin-bottom: 20px;
    animation: bounce 1s infinite alternate;
}}
@keyframes bounce {{
    from {{ transform: translateY(0); }}
    to {{ transform: translateY(-10px); }}
}}

/* ボタン */
.button {{
    display: inline-block;
    background: linear-gradient(45deg, {theme_color}, #7289DA);
    color: #FFF;
    text-decoration: none;
    padding: 14px 28px;
    border-radius: 8px;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: transform 0.2s, opacity 0.2s;
}}
.button:hover {{
    transform: translateY(-2px);
    opacity: 0.95;
}}

/* スコープリスト */
.scope-list {{
    text-align: left;
    margin-top: 24px;
}}
.scope-item {{
    margin-bottom: 12px;
}}
.scope-item b {{
    color: #FFF;
}}

/* レスポンシブ */
@media (max-width: 480px) {{
    .card {{
        padding: 32px 20px;
    }}
    .icon {{
        font-size: 48px;
    }}
    .button {{
        padding: 12px 20px;
        font-size: 14px;
    }}
}}
</style>
</head>
<body>
<div class="card">{body_html}</div>
</body>
</html>"""


def get_start_page(guild_name, scopes, oauth_url):
    # スコープリストHTML
    scope_list_html = "".join(
        f"<div class='scope-item'>"
        f"<b>{SCOPE_DESCRIPTIONS.get(s, {'name': s})['name']}</b>: "
        f"{SCOPE_DESCRIPTIONS.get(s, {'desc': 'カスタムスコープ'})['desc']}"
        f"</div>"
        for s in scopes
    )

    # 本格的な規約とライセンス情報
    body = f"""
    <div class="icon">🛡️</div>
    <h1 style="margin-bottom:12px; font-size:28px;">{guild_name} の認証</h1>
    <p style="margin-bottom:24px; font-size:16px; color:#CCC;">以下のスコープにアクセスします。</p>
    <div class="scope-list">{scope_list_html}</div>

    <!-- 規約同意チェックボックス -->
    <div style="margin-top:24px; text-align:left; font-size:14px; color:#CCC;">
        <input type="checkbox" id="agree" onchange="toggleButton()"> 
        <label for="agree">利用規約とライセンス情報に同意します</label>
    </div>

    <!-- 認証ボタン -->
    <a id="authButton" href="{oauth_url}" class="button" style="margin-top:20px; pointer-events:none; opacity:0.5;">Discordで認証</a>

    <!-- 利用規約 / ライセンスボタン -->
    <div style="margin-top:16px;">
        <button class="modal-btn" onclick="openModal('termsModal')">利用規約</button>
        <button class="modal-btn" onclick="openModal('licenseModal')">ライセンス情報</button>
    </div>

    <!-- モーダル: 利用規約 -->
    <div id="termsModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('termsModal')">&times;</span>
            <h2>利用規約</h2>
            <p>1. 本サービスはDiscord OAuth2を利用した認証を提供します。</p>
            <p>2. 不正アクセス、スパム、他者の権利を侵害する行為は禁止されています。</p>
            <p>3. 認証情報や取得データは当サービスでのみ使用され、安全に保護されます。</p>
            <p>4. 利用者は自己責任でサービスを使用するものとし、損害発生に対する責任は負いません。</p>
            <p>5. 本サービスは予告なく変更または終了することがあります。</p>
            <p>6. 本規約は法的拘束力を持ち、同意なしに利用できません。</p>
        </div>
    </div>

    <!-- モーダル: ライセンス情報 -->
    <div id="licenseModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('licenseModal')">&times;</span>
            <h2>ライセンス情報</h2>
            <p>本サービスおよび付属コードはMITライセンスの下で提供されます。</p>
            <p>MITライセンス概要:</p>
            <ul>
                <li>ソフトウェアを商用・非商用で自由に使用可能</li>
                <li>コピー、改変、再配布が可能</li>
                <li>著作権表示およびライセンス表示を保持する必要があります</li>
                <li>無保証: 著作者は利用による損害について責任を負いません</li>
            </ul>
        </div>
    </div>

    <script>
    function toggleButton() {{
        const cb = document.getElementById('agree');
        const btn = document.getElementById('authButton');
        if(cb.checked) {{
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = 1;
        }} else {{
            btn.style.pointerEvents = 'none';
            btn.style.opacity = 0.5;
        }}
    }}

    function openModal(id) {{
        document.getElementById(id).style.display = 'block';
    }}
    function closeModal(id) {{
        document.getElementById(id).style.display = 'none';
    }}
    </script>

    <style>
    /* モーダル共通 */
    .modal {{
        display:none;
        position:fixed;
        z-index:1000;
        left:0; top:0;
        width:100%; height:100%;
        overflow:auto;
        background-color: rgba(0,0,0,0.7);
    }}
    .modal-content {{
        background:#2B2D31;
        margin:10% auto;
        padding:20px;
        border-radius:12px;
        max-width:500px;
        color:#F2F3F5;
        box-shadow:0 12px 24px rgba(0,0,0,0.5);
        animation:slideDown 0.3s ease;
    }}
    @keyframes slideDown {{
        from {{ transform: translateY(-50px); opacity:0; }}
        to {{ transform: translateY(0); opacity:1; }}
    }}
    .close {{
        float:right;
        font-size:24px;
        cursor:pointer;
        color:#AAA;
    }}
    .close:hover {{ color:#FFF; }}
    .modal-btn {{
        background: #5865F2;
        color:#FFF;
        border:none;
        border-radius:8px;
        padding:8px 16px;
        margin-right:8px;
        cursor:pointer;
        font-weight:500;
        transition:0.2s;
    }}
    .modal-btn:hover {{
        background: #7289DA;
    }}
    </style>
    """

    return get_html_template(f"{guild_name} 認証", body)


def get_success_page():
    return get_html_template("認証成功", "<div class='icon'>✅</div><h1>認証完了！</h1><p>ロールが付与されました。</p>", "#23A559")

def get_error_page(msg):
    return get_html_template("エラー", f"<div class='icon'>❌</div><h1>エラー</h1><p>{msg}</p>", "#F23F42")

# ================================================================
# BOT設定
# ================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================================================================
# UI: 認証ボタン
# ================================================================
class VerificationView(discord.ui.View):
    def __init__(self, panel_id: str):
        super().__init__(timeout=None)
        self.panel_id = panel_id

    @discord.ui.button(label="認証する", style=discord.ButtonStyle.primary, emoji="✅", custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        start_auth_url = f"{BASE_URL}/auth/{self.panel_id}/{interaction.user.id}"
        embed = discord.Embed(
            title="認証手続き",
            description=f"[こちらのリンクを開いて認証を進めてください]({start_auth_url})",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ================================================================
# 起動時
# ================================================================
@bot.event
async def on_ready():
    global session
    if session is None:
        session = aiohttp.ClientSession()
    await setup_webapp()

    # 既存の認証ビューを復元
    for panel_id in db.get("panels", {}):
        bot.add_view(VerificationView(panel_id))

    # スラッシュコマンドを同期
    synced = await bot.tree.sync()
    
    print(f"✅ Logged in as {bot.user}")
    print(f"🌐 Callback URL: {BASE_URL}/callback")
    print(f"🔄 同期されたコマンド数: {len(synced)}")
    for cmd in synced:
        print(f" - {cmd.name}")

# ================================================================
# Slashコマンド
# ================================================================
@bot.tree.command(name="panel_create", description="認証パネルを作成します。")
async def panel_create(interaction: discord.Interaction,
                       title: str = "埋め込みのタイトル",
                       description: str = "埋め込みの説明文",
                       role: discord.Role = None,
                       scope: str = "identify",
                       webhook_channel: discord.TextChannel = None,
                       image_url: str = None,
                       embed_color: str = "#5865F2",
                       custom_redirect_url: str = None):

    await interaction.response.defer(ephemeral=True)

    if not role or not webhook_channel:
        return await interaction.followup.send("ロールまたはログ送信チャンネルが指定されていません。", ephemeral=True)

    embed_color_int = int(embed_color.lstrip("#"), 16)

    scopes = sorted(set(s.strip().lower() for s in scope.split(",")))
    invalid_scopes = [s for s in scopes if s not in SCOPE_DESCRIPTIONS]
    if invalid_scopes:
        return await interaction.followup.send(
        f"無効なスコープがあります。: `{', '.join(invalid_scopes)}`\n"
        f"または , で区切られていない可能性があります。`\n"
        f"利用可能: `{'`, `'.join(SCOPE_DESCRIPTIONS.keys())}`", ephemeral=True
    )

    bot_member = interaction.guild.me
    if bot_member.top_role <= role:
        return await interaction.followup.send(f"BOTのロールが `{role.name}` より下です。", ephemeral=True)

    try:
        webhook = await webhook_channel.create_webhook(name=f"{bot.user.name} 認証ログ")
    except discord.Forbidden:
        return await interaction.followup.send("Webhook作成権限がありません。", ephemeral=True)

    embed = discord.Embed(title=title, description=description, color=embed_color_int)
    if image_url:
        embed.set_image(url=image_url)

    msg = await interaction.channel.send(embed=discord.Embed(title="生成中...", color=discord.Color.light_grey()))
    panel_id = str(msg.id)
    await msg.edit(embed=embed, view=VerificationView(panel_id))

    db["panels"][panel_id] = {
        "guild_id": interaction.guild.id,
        "role_id": role.id,
        "scopes": scopes,
        "webhook_url": webhook.url,
        "embed_color": embed_color,
        "redirect_uri": custom_redirect_url or f"{BASE_URL}/callback"
    }
    save_db()
    await interaction.followup.send("✅ 認証パネルを作成しました。", ephemeral=True)

# ================================================================
# OAuth2ハンドラー
# ================================================================
async def handle_auth_start(request):
    panel_id = request.match_info["panel_id"]
    user_id = request.match_info["user_id"]
    panel = db["panels"].get(panel_id)
    if not panel:
        return web.Response(text=get_error_page("無効な認証パネルです。"), content_type="text/html")

    guild = bot.get_guild(panel["guild_id"])
    if not guild:
        return web.Response(text=get_error_page("サーバーが見つかりません。"), content_type="text/html")

    state = str(uuid.uuid4())
    db["states"][state] = {
        "user_id": int(user_id),
        "panel_id": panel_id,
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    }
    save_db()

    oauth_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={quote(panel['redirect_uri'])}&response_type=code"
        f"&scope={quote(' '.join(panel['scopes']))}&state={state}&prompt=consent"
    )
    return web.Response(text=get_start_page(guild.name, panel["scopes"], oauth_url), content_type="text/html")

async def handle_callback(request):
    code, state = request.query.get("code"), request.query.get("state")
    state_data = db["states"].get(state)
    if not state_data:
        return web.Response(text=get_error_page("セッションが無効です。"), content_type="text/html")

    if datetime.datetime.fromisoformat(state_data["expires_at"]) < datetime.datetime.utcnow():
        db["states"].pop(state, None)
        save_db()
        return web.Response(text=get_error_page("セッションが期限切れです。"), content_type="text/html")

    panel = db["panels"].get(state_data["panel_id"])
    if not panel:
        return web.Response(text=get_error_page("認証パネルが見つかりません。"), content_type="text/html")

    # OAuthトークン取得
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": panel["redirect_uri"],
    }
    async with session.post("https://discord.com/api/v10/oauth2/token", data=token_data) as resp:
        if resp.status != 200:
            return web.Response(text=get_error_page("トークン交換に失敗しました。"), content_type="text/html")
        token_json = await resp.json()

    headers = {"Authorization": f"Bearer {token_json['access_token']}"}
    async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as r:
        user = await r.json()

    # 取得した情報を info.txt にまとめる
    info_content = json.dumps(user, ensure_ascii=False, indent=4)
    info_file = io.BytesIO(info_content.encode("utf-8"))
    info_file.name = "info.txt"

    guild = bot.get_guild(panel["guild_id"])
    member = await guild.fetch_member(state_data["user_id"])
    role = guild.get_role(panel["role_id"])
    if not all([guild, member, role]):
        return web.Response(text=get_error_page("必要な情報が見つかりません。"), content_type="text/html")

    try:
        await member.add_roles(role, reason="OAuth認証による自動付与")
    except Exception as e:
        print(f"ロール付与失敗: {e}")

    user_avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get("avatar") else None
    webhook = discord.Webhook.from_url(panel["webhook_url"], session=session)
    embed = discord.Embed(
        title="✅ 新規認証完了",
        description=f"{member.mention} に `{role.name}` を付与しました。",
        color=discord.Color.green()
    )
    embed.set_author(name=f"{user['username']}#{user['discriminator']}", icon_url=user_avatar_url)
    await webhook.send(embed=embed, file=discord.File(fp=info_file))

    db["states"].pop(state, None)
    save_db()
    return web.Response(text=get_success_page(), content_type="text/html")

# ================================================================
# Webサーバー起動
# ================================================================
async def setup_webapp():
    app = web.Application()
    app.router.add_get("/auth/{panel_id}/{user_id}", handle_auth_start)
    app.router.add_get("/callback", handle_callback)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌐 Webサーバー起動: http://0.0.0.0:{PORT}")

# ================================================================
# BOT起動
# ================================================================
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
