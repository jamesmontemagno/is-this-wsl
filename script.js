const $ = (id) => document.getElementById(id);

function browserFromUserAgent(userAgent) {
  const patterns = [
    ["Edge", /Edg(?:e|A|iOS)?\/([\d.]+)/i],
    ["Opera", /OPR\/([\d.]+)/i],
    ["Chrome", /(?:Chrome|CriOS)\/([\d.]+)/i],
    ["Firefox", /(?:Firefox|FxiOS)\/([\d.]+)/i],
    ["Safari", /Version\/([\d.]+).*Safari/i]
  ];

  return patterns.reduce((result, [name, pattern]) => {
    const match = userAgent.match(pattern);
    return result.name === "Unknown browser" && match ? { name, version: match[1] } : result;
  }, { name: "Unknown browser", version: "" });
}

function shorten(value, maxLength) {
  return value.length > maxLength ? `${value.slice(0, maxLength - 1)}…` : value;
}

function renderEnvironment(data) {
  const { os, wsl, browser, kernel } = data;
  const clientBrowser = browser.name === "Unknown browser"
    ? browserFromUserAgent(navigator.userAgent)
    : browser;

  $("wsl-card").classList.toggle("not-wsl", !wsl.isWsl);
  $("wsl-title").textContent = wsl.isWsl ? "Yes, this is WSL!" : "No WSL detected here";
  $("wsl-description").textContent = wsl.isWsl
    ? `Running ${wsl.distro || "a Linux distribution"} through Windows Subsystem for Linux.`
    : "This looks like a native Linux environment (or WSL is keeping a low profile).";
  $("wsl-badge").textContent = wsl.isWsl ? `WSL ${wsl.version || "?"}` : "NATIVE";

  $("os-name").textContent = os.name;
  $("os-meta").textContent = `${os.platform} · ${os.architecture}${os.version ? ` · v${os.version}` : ""}`;
  $("distro-name").textContent = shorten(wsl.distro || os.name, 24);
  $("distro-meta").textContent = wsl.isWsl ? "The Linux flavor inside WSL" : "Your Linux flavor";
  $("kernel-name").textContent = shorten(kernel, 27);
  $("kernel-meta").textContent = wsl.isWsl ? `WSL ${wsl.version || ""} kernel` : "The core beneath it all";
  $("browser-name").textContent = `${clientBrowser.name}${clientBrowser.version ? ` ${clientBrowser.version}` : ""}`;
  $("browser-meta").textContent = "The window you used to get here";
  $("language-pill").textContent = `language ${navigator.language || "—"}`;
  $("timezone-pill").textContent = `timezone ${Intl.DateTimeFormat().resolvedOptions().timeZone || "—"}`;
  $("checked-at").textContent = `checked ${new Date(data.checkedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

async function loadEnvironment() {
  $("refresh-button").disabled = true;
  $("refresh-button").querySelector(".refresh-icon").textContent = "↻";

  try {
    const response = await fetch("/api/environment", { cache: "no-store" });
    if (!response.ok) throw new Error(`Environment request failed with ${response.status}`);
    renderEnvironment(await response.json());
  } catch (error) {
    $("wsl-title").textContent = "Could not read the setup";
    $("wsl-description").textContent = "The environment report is unavailable right now.";
    $("wsl-badge").textContent = "RETRY";
    console.error(error);
  } finally {
    $("refresh-button").disabled = false;
  }
}

$("refresh-button").addEventListener("click", loadEnvironment);
loadEnvironment();
