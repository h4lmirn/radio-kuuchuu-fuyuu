<h1 align="center">ラジオ空中浮遊</h1>

<p align="center"><b>AIとテックと世界の、きのうの気になるニュースを毎朝。<br>締めに、中国茶のブランドをひとつ紹介します。</b></p>

<p align="center">
  <a href="https://h4lmirn.github.io/radio-kuuchuu-fuyuu/"><img src="https://img.shields.io/badge/%E2%96%B6%20ON%20AIR-Kuuchuu%20Fuyuu-ffd028?style=for-the-badge&labelColor=ff4468" alt="ラジオ空中浮遊を聴く"></a>
</p>

- キャスターは changsama。声は Muse（AI音声合成）です
- 配信は、台本（JSON）と音声を置いて push するだけ。動画ではなく HTML の番組で、再生に合わせてスライド・字幕・キャラ・リンクカードが動きます
- ニュースの画像は、記事のサイトが共有用に公開している画像（OGP）をそのサイトから直接表示します。画像を保存したり配り直したりはしません
- 音声の公開は直近 30 日分だけ。台本はずっと残るので、過去の回も文字で読めます

## 中身

```
station.json         局の自己紹介（名前・放送の内容・ロゴ・クレジット・音声の置き方）
episodes.json        回の一覧
episodes/<日付>-<言語>.json  台本とタイミング
audio/<日付>-<言語>.mp3     声（main にはコミットしない。publish.sh が直近の分だけ gh-pages に載せる）
logo.svg             ロゴ
character/           キャスター（changsama の画像）
tools/publish.sh     GitHub Pages への公開
docs/formats.md      JSON の形
```

## ライセンスとクレジット

- プログラム（`index.html`、`tools/`）：MIT License。[myradio](https://github.com/monoradio102/myradio) テンプレート（お手本の局「ものラジオ」）を使って開局しました
- 台本（`episodes/`、`episodes.json`）：各回の出典リンク先の記事に基づきます
- キャラ（`character/`）：キャラクター「changsama」は原田遥の分身キャラクターです。AIで生成した画像をもとに作成しました。無断での使用・再配布はできません
- 声：Muse（AI音声合成）
- 天気：Open-Meteo（CC BY 4.0）
