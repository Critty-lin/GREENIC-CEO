/* 数据服务地址。
 *
 * 线上游戏使用 Cloudflare Pages Functions：
 *   https://greenic-ceo-api.pages.dev
 * 本地用 `python3 server.py` 打开时自动走同源，不会把开发数据写到线上。
 * 自己部署时把下面的地址换成你的 Pages / Worker 地址，结尾不要带斜杠。
 */
(function () {
  const local =
    location.protocol === "file:" ||
    ["localhost", "127.0.0.1", "::1", "[::1]"].indexOf(location.hostname) >= 0;
  window.ADVN_API = local ? "" : "https://greenic-ceo-api.pages.dev";
})();
