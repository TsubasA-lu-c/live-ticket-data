# live-ticket-data 運用ガイド

> このリポジトリでの作業は sonnet が担当。
> 詳細ルールは COLLECTION_RULES.md を参照。
> **作業前に必ず `git pull origin main` を実行してから作業を開始すること。**
> **必ず validate.py を通過してから push すること。**

---

## 作業の種類と手順

### A. アーティスト追加（新規）

1. **既存データの読み込み**
   - `data/artists.json` を読む（既存ID・artistId を把握）
   - `data/artist/` の一覧を取得（ファイル名から既存artistId を把握）

2. **正規名称の解決**（COLLECTION_RULES.md §3.5）
   - 入力名をウェブ検索して公式サイトで正規表記を確認
   - id は英小文字スネーク（例: `mr_children`）

3. **情報収集**（COLLECTION_RULES.md §4）
   - 公式サイトからツアー・公演・抽選情報を取得
   - 不明な値は null（推測で埋めない）

4. **ファイルの作成・更新**
   - `data/artist/{id}.json` を作成（下記テンプレート参照）
   - `data/artists.json` に一覧エントリを追記

5. **バリデーション**（必須）
   ```
   python3 tools/validate.py
   ```
   エラーがあれば修正して再実行。

6. **manifest 更新**（必須）
   ```
   python3 tools/update_manifest.py
   ```

7. **commit & push**
   ```
   git add data/artist/{id}.json data/artists.json data/manifest.json
   git commit -m "add: {アーティスト名}を追加"
   git push origin main
   ```

---

### B. アーティスト更新（鮮度更新・新情報追加）

1. `data/artist/{id}.json` を読む（既存データを把握）
2. 公式サイト・チケットサイトを確認（最新ツアー・抽選情報）
3. 変更を反映（終了データの除外は COLLECTION_RULES.md §5.1 に従う）
4. `python3 tools/validate.py` を実行（エラーなし確認）
5. `python3 tools/update_manifest.py` を実行
6. `git add data/artist/{id}.json data/artists.json data/manifest.json && git commit -m "update: {アーティスト名}情報更新" && git push origin main`

---

---

## 直列5件刻み実行の原則（C・D・E 共通）

複数アーティストを処理する場合は**5組ずつ直列に処理しcommitを積む**。
途中でセッションリミットに達しても完了済み分はpush済みのため、再実行時は残りのアーティストからのみ再開できる。

### 役割分担（違反厳禁）

| 役割 | 書いてよいファイル | 触ってはいけないファイル |
|---|---|---|
| **バッチサブエージェント** | `data/artist/{担当id}.json` のみ | `data/artists.json` / `data/manifest.json` / 他アーティストのファイル |
| **メインエージェント** | `data/artists.json` / `data/manifest.json` | （バッチ完了後のみ操作） |

### 直列実行フロー

```
メイン: 対象アーティストを5組ずつのバッチに分割
  ↓
【バッチ①】サブエージェントを foreground で起動（5組・完了を待つ）
  ↓ 完了
メイン: data/artists.json を更新 → validate.py → commit & push
  ↓
【バッチ②】サブエージェントを foreground で起動（次の5組・完了を待つ）
  ↓ 完了
メイン: data/artists.json を更新 → validate.py → commit & push
  ↓ …繰り返し…
全バッチ完了後: update_manifest.py → commit & push
```

- サブエージェントは `run_in_background: false`（foreground）で起動する
- 各バッチ完了後に必ず `validate.py` を通してから commit & push する
- manifest 更新（`update_manifest.py`）は**全バッチ完了後に1回だけ**行う

### バッチサブエージェントへの指示テンプレート

各サブエージェントには以下を伝える:
- 担当アーティストIDの一覧（5組以内）
- 実施内容（追加 or 更新 or 更新+終了掃除）
- **`data/artist/{id}.json` のみ書くこと（artists.json/manifest.json は触らない）**
- 完了後に担当アーティストの `lastVerifiedAt`（更新日時）を報告すること
- validate.py は**実行しない**（メインが一括で行う）

---

### C. 毎週の鮮度更新（/refresh-hot）

Hot tier（3ヶ月以内に抽選締切があるアーティスト）のみを更新する。

1. 全 `data/artist/*.json` を読み込み、Hot tier を抽出
   - 判定: `lotteries[].entryEndAt` が今日から90日以内かつ未来のものが1件以上あるか
2. 抽出したアーティストを5組ずつのバッチに分割
3. 直列5件刻み実行の原則に従い、バッチごとに順番に処理:
   - サブエージェント（haiku）をforegroundで起動 → 完了を待つ
   - `data/artists.json` の `lastVerifiedAt` を更新
   - `python3 tools/validate.py`（エラーがあれば修正）
   - `git add data/artist/... data/artists.json && git commit -m "refresh: Hot tier {アーティスト名}など" && git push origin main`
4. 全バッチ完了後: `python3 tools/update_manifest.py` → `git add data/manifest.json && git commit -m "update: manifest" && git push origin main`

---

### D. 月次の全件更新（/refresh-all）

全アーティストを更新 + 終了ツアーの掃除を行う。

1. `data/artists.json` を読んで全 id を取得
2. 全アーティストを5組ずつのバッチに分割
3. 直列5件刻み実行の原則に従い、バッチごとに順番に処理:
   - サブエージェント（haiku）をforegroundで起動 → 完了を待つ（終了ツアーの掃除も実施）
   - `data/artists.json` の `lastVerifiedAt` を更新
   - `python3 tools/validate.py`（エラーがあれば修正）
   - `git add data/artist/... data/artists.json && git commit -m "refresh: {アーティスト名}など更新" && git push origin main`
4. 全バッチ完了後: `python3 tools/update_manifest.py` → `git add data/manifest.json && git commit -m "update: manifest" && git push origin main`

---

### E. 新規アーティスト追加バッチ（/add-artists）

1. 追加対象リストを確認（ジャンルバランスを考慮）
2. 対象を5組ずつのバッチに分割
3. 直列5件刻み実行の原則に従い、バッチごとに順番に処理:
   - サブエージェント（sonnet）をforegroundで起動 → 完了を待つ
   - `data/artists.json` に追加5組のエントリを追記
   - `python3 tools/validate.py`（エラーがあれば修正）
   - `git add data/artist/... data/artists.json && git commit -m "add: {アーティスト名}など" && git push origin main`
4. 全バッチ完了後: `python3 tools/update_manifest.py` → `git add data/manifest.json && git commit -m "update: manifest" && git push origin main`

---

## スキーマテンプレート

### `data/artists.json` への追記エントリ
```json
{
  "id": "artist_id",
  "name": "アーティスト正規名",
  "aliases": ["略称1", "略称2"],
  "genre": "バンド|ソロ|アイドル|K-POP|声優|ユニット|ヒップホップ",
  "imageUrl": null,
  "source": "system",
  "sourceUrl": "https://公式サイトURL",
  "lastVerifiedAt": "2026-06-14T00:00:00+09:00"
}
```

### `data/artist/{id}.json` テンプレート
```json
{
  "artistId": "artist_id",
  "tours": [
    {
      "id": "artistid_tourslug_2026",
      "artistId": "artist_id",
      "title": "ツアー名",
      "startDate": "2026-08-01T00:00:00+09:00",
      "endDate": "2026-09-30T00:00:00+09:00",
      "prices": [
        {"label": "指定席", "amount": 8800}
      ],
      "source": "system",
      "sourceUrl": "https://公式URL",
      "lastVerifiedAt": "2026-06-14T00:00:00+09:00"
    }
  ],
  "performances": [
    {
      "id": "tourId_会場省略_mmdd",
      "tourId": "上記tourのid",
      "venue": "会場名（正式名称）",
      "performanceAt": "2026-08-01T18:00:00+09:00",
      "doorOpenAt": "2026-08-01T17:00:00+09:00",
      "kind": "oneman",
      "eventName": null,
      "source": "system",
      "sourceUrl": "https://公式URL",
      "lastVerifiedAt": "2026-06-14T00:00:00+09:00"
    }
  ],
  "lotteries": [
    {
      "id": "tourId_fc先行",
      "tourId": "上記tourのid",
      "type": "FC先行",
      "entryStartAt": "2026-06-01T12:00:00+09:00",
      "entryEndAt": "2026-06-20T23:59:00+09:00",
      "resultAt": "2026-06-30T12:00:00+09:00",
      "paymentStartAt": null,
      "paymentEndAt": null,
      "performanceIds": ["上記performanceのid"],
      "source": "system",
      "sourceUrl": "https://公式URL",
      "lastVerifiedAt": "2026-06-14T00:00:00+09:00"
    }
  ]
}
```

---

## モデル運用ルール（サブエージェント）

バッチサブエージェントを起動する際は、作業種別に応じてモデルを使い分ける。

| 作業 | モデル | 理由 |
|------|--------|------|
| `/add-artists`（新規追加） | `sonnet` | WebFetchした生HTMLから情報を正確に抽出する必要がある。質が重要で後からのリカバリーが面倒 |
| `/refresh-hot`（鮮度更新） | `haiku` | 既存データがあり差分チェックが主体。単純な構造化タスクなのでhaikuで十分 |
| `/refresh-all`（全件更新） | `haiku` | 同上 |

Agent呼び出し時に `model: "sonnet"` または `model: "haiku"` を明示すること。

---

## よくある間違いと防止策

| 間違い | 防止策 |
|-------|-------|
| IDを重複させる | 作業前に必ず data/artist/ の全ファイルを読んで既存IDを把握 |
| tourIdの参照ミス | performance/lottery の tourId は同一ファイル内の tour.id と一致させる |
| 日時にオフセットなし | 必ず `+09:00` を付ける（例: `2026-08-01T18:00:00+09:00`） |
| 推測で埋める | 不明な値は必ず null |
| validate.py をスキップ | push 前に必ず実行（エラーがあれば修正してから） |
| manifest を手動更新 | update_manifest.py を使う（hash の手動計算は禁止） |
