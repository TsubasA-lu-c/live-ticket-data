# live-ticket-data 運用ガイド

> このリポジトリでの作業は sonnet が担当。
> 詳細ルールは COLLECTION_RULES.md を参照。
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

### C. 複数アーティスト一括更新（/refresh-artists）

上記 B を登録済み全アーティストに適用する。

1. `data/artists.json` を読んで全 id を取得
2. 各アーティストについて B の手順 1〜3 を実施
3. 全て完了後に `python3 tools/validate.py`
4. `python3 tools/update_manifest.py`
5. まとめて commit & push

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

## よくある間違いと防止策

| 間違い | 防止策 |
|-------|-------|
| IDを重複させる | 作業前に必ず data/artist/ の全ファイルを読んで既存IDを把握 |
| tourIdの参照ミス | performance/lottery の tourId は同一ファイル内の tour.id と一致させる |
| 日時にオフセットなし | 必ず `+09:00` を付ける（例: `2026-08-01T18:00:00+09:00`） |
| 推測で埋める | 不明な値は必ず null |
| validate.py をスキップ | push 前に必ず実行（エラーがあれば修正してから） |
| manifest を手動更新 | update_manifest.py を使う（hash の手動計算は禁止） |
