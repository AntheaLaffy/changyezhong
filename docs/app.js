(() => {
  const KEY = "cyz-nsfw";
  const allowed = localStorage.getItem(KEY) === "1";

  document.querySelectorAll("a[data-nsfw='true']").forEach((a) => {
    a.addEventListener("click", (e) => {
      if (localStorage.getItem(KEY) === "1") return;
      e.preventDefault();
      if (confirm("本章含成人内容。确认已满十八岁并继续？")) {
        localStorage.setItem(KEY, "1");
        location.href = a.href;
      }
    });
  });

  const main = document.querySelector("main.read");
  if (main && main.dataset.nsfw === "true" && !allowed) {
    const gate = document.createElement("div");
    gate.className = "gate";
    gate.innerHTML = `<div class="gate-box">
      <h2>夜律</h2>
      <p>本章含成人描写。请确认已满十八岁。</p>
      <button type="button" id="ok">进入</button>
      <button type="button" class="ghost" id="no">返回目录</button>
    </div>`;
    document.body.appendChild(gate);
    gate.querySelector("#ok").onclick = () => {
      localStorage.setItem(KEY, "1");
      gate.hidden = true;
    };
    gate.querySelector("#no").onclick = () => {
      location.href = "../index.html";
    };
  }

  document.addEventListener("keydown", (e) => {
    const pager = document.querySelector(".pager");
    if (!pager) return;
    const links = [...pager.querySelectorAll("a")];
    if (e.key === "ArrowLeft") links[0]?.click();
    if (e.key === "ArrowRight") links[1]?.click();
  });
})();
