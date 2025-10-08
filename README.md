# Discord OAuth2 認証パネル BOT

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 概要

このBOTは **Discord OAuth2 認証パネル** を簡単に作成できるBOTです。
ユーザーがDiscordでOAuth認証を行うことで、指定されたロールを自動付与できます。

✅ **特徴**

* 複数スコープ対応（identify, email, guilds など）
* 認証情報をWebhookで安全に送信
* 利用規約・ライセンス確認モーダル付き認証ページ
* 自動でユーザーにロールを付与
* Webサーバー統合でOAuth2フローを簡単に管理

---

## 特徴詳細

* **簡単パネル作成**：スラッシュコマンド `/panel_create` で数秒でパネル作成
* **安全なデータ送信**：ユーザー情報は `info.txt` としてWebhook送信
* **UI改善**：利用規約チェック、モーダル表示、レスポンシブ対応
* **複数スコープ**：`,` 区切りで `identify,email,guilds` など同時取得可能
* **ロール自動付与**：認証後、自動で指定ロールを付与

---

## Discord側の設定

1. **アプリケーション作成**

   * [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
   * 新しいアプリケーションを作成

2. **OAuth2設定**

   * 左メニューの「OAuth2」→「URL Generator」
   * **スコープ**に `bot` と `applications.commands` を追加
   * **Botの権限**に `Manage Roles`, `Send Messages`, `Embed Links` を付与
   * `redirect_uri` に `https://your-domain.com/callback` を追加
   * 生成されたURLはテストや自動認証に使用

3. **Bot設定**

   * 「Bot」タブから BOT を作成
   * 「Token」をコピーして `BOT_TOKEN` に設定
   * 「Privileged Gateway Intents」から `Server Members Intent` を有効化

4. **サーバー招待**

   * OAuth2 URL でBotをサーバーに招待
   * Botがロール付与対象より上のロールにいることを確認

---

## 環境変数

BOT起動前に以下を設定してください：

```bash
export BOT_TOKEN="あなたのBOTトークン"
export CLIENT_ID="アプリケーションID"
export CLIENT_SECRET="クライアントシークレット"
export BASE_URL="https://your-domain.com"
export PORT=8080
```

Windows PowerShell の場合：

```powershell
$env:BOT_TOKEN="あなたのBOTトークン"
```

---

## インストール

```bash
git clone https://github.com/yourusername/discord-oauth-panel.git
cd discord-oauth-panel
pip install -r requirements.txt
python bot.py
```

---

## 使用方法

### 認証パネル作成例

```txt
/panel_create
title: サーバー認証
description: Discord OAuth2認証でロール付与
role: @Verified
scope: identify,email,guilds
webhook_channel: #verification-log
use_custom_redirect: false
```

作成後、指定チャンネルに認証ボタンが表示されます。
ユーザーはチェックボックスに同意後、認証ボタンで認証完了。

---

## 複数スコープ指定例

* `identify,email,guilds`
* `identify,guilds.members.read`
* スペースではなくカンマ `,` で区切ること

---

## Webサーバー公開方法

1. **リバースプロキシ使用（推奨）**

   * Nginx または Caddy で `BASE_URL` を公開
   * HTTPS化して安全な通信を確保

2. **クラウドサーバー上で起動**

   * Ubuntu / Debian / CentOS に Python 3.11+ をインストール
   * `nohup python bot.py &` などで常時起動

3. **ローカルPCでテスト**

   * `localhost:8080` で動作確認可能
   * 公開時は必ず `BASE_URL` を正しいドメインに変更

---

## 対応スコープ

* `identify`：ユーザー情報（ID, 名前, アバター）
* `email`：メールアドレス
* `connections`：外部連携情報
* `guilds`：参加サーバー一覧
* `guilds.join`：サーバー参加
* `guilds.members.read`：サーバーメンバー情報

---

## 貢献方法

1. リポジトリを Fork
2. 新しいブランチで開発

```bash
git checkout -b feature/新機能名
```

3. コード修正 / 機能追加
4. PR（プルリクエスト）作成

### コード規約

* Python 3.11+
* `black` または `autopep8` でフォーマット
* コメントを丁寧に書く

---

## ライセンス

MIT License
詳細は [LICENSE](LICENSE) を参照

---

## 注意事項

* 本BOTは **自己責任** で使用してください
* 不正アクセスやスパム目的での使用は禁止
* OAuthで取得した情報は安全に管理してください
* BOTは管理者が意図する権限範囲内で使用してください

---

## 開発者

ゆっくりーむ (Yukkurim)

---

💡 **Tip**:
認証パネルはテスト環境で十分に確認後、公開サーバーで使用してください。


