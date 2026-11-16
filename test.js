// Simple Snake game in pure JavaScript using canvas.
// To use this file, create an HTML file in the same folder like:
// <html>
//   <body style="margin:0;background:#111;">
//     <canvas id="game" width="400" height="400"></canvas>
//     <script src="test.js"></script>
//   </body>
// </html>

(function () {
  const canvas = document.getElementById("game");
  if (!canvas) {
    console.error("Canvas with id 'game' not found.");
    return;
  }

  const ctx = canvas.getContext("2d");
  const tileSize = 20;
  const tilesX = canvas.width / tileSize;
  const tilesY = canvas.height / tileSize;

  let snake = [
    { x: 8, y: 10 },
    { x: 7, y: 10 },
    { x: 6, y: 10 },
  ];

  let direction = { x: 1, y: 0 }; // moving right
  let nextDirection = { x: 1, y: 0 };
  let food = randomFood();
  let gameOver = false;
  let score = 0;
  let speedMs = 130;
  let lastTime = 0;
  let paused = false;

  window.addEventListener("keydown", (e) => {
    switch (e.key) {
      case "ArrowUp":
      case "w":
      case "W":
        if (direction.y === 0) nextDirection = { x: 0, y: -1 };
        break;
      case "ArrowDown":
      case "s":
      case "S":
        if (direction.y === 0) nextDirection = { x: 0, y: 1 };
        break;
      case "ArrowLeft":
      case "a":
      case "A":
        if (direction.x === 0) nextDirection = { x: -1, y: 0 };
        break;
      case "ArrowRight":
      case "d":
      case "D":
        if (direction.x === 0) nextDirection = { x: 1, y: 0 };
        break;
      case " ":
        if (gameOver) restart();
        break;
      case "p":
      case "P":
      case "Escape":
        if (!gameOver) {
          paused = !paused;
        }
        break;
    }
  });

  function restart() {
    snake = [
      { x: 8, y: 10 },
      { x: 7, y: 10 },
      { x: 6, y: 10 },
    ];
    direction = { x: 1, y: 0 };
    nextDirection = { x: 1, y: 0 };
    food = randomFood();
    gameOver = false;
    score = 0;
    speedMs = 130;
    paused = false;
  }

  function randomFood() {
    let pos;
    while (true) {
      pos = {
        x: Math.floor(Math.random() * tilesX),
        y: Math.floor(Math.random() * tilesY),
      };
      if (!snake.some((s) => s.x === pos.x && s.y === pos.y)) break;
    }
    return pos;
  }

  function update() {
    if (gameOver || paused) return;

    direction = nextDirection;

    const head = snake[0];
    const newHead = { x: head.x + direction.x, y: head.y + direction.y };

    // Check wall collision
    if (
      newHead.x < 0 ||
      newHead.x >= tilesX ||
      newHead.y < 0 ||
      newHead.y >= tilesY
    ) {
      gameOver = true;
      return;
    }

    // Check self collision
    if (snake.some((s) => s.x === newHead.x && s.y === newHead.y)) {
      gameOver = true;
      return;
    }

    snake.unshift(newHead);

    // Check food
    if (newHead.x === food.x && newHead.y === food.y) {
      score++;
      // slightly increase speed
      speedMs = Math.max(60, speedMs - 3);
      food = randomFood();
    } else {
      snake.pop();
    }
  }

  function drawGrid() {
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 1;
    for (let x = 0; x <= canvas.width; x += tileSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += tileSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }

  function draw() {
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawGrid();

    // Draw food
    ctx.fillStyle = "#e74c3c";
    ctx.fillRect(food.x * tileSize, food.y * tileSize, tileSize, tileSize);

    // Draw snake
    snake.forEach((segment, index) => {
      ctx.fillStyle = index === 0 ? "#2ecc71" : "#27ae60";
      ctx.fillRect(
        segment.x * tileSize + 1,
        segment.y * tileSize + 1,
        tileSize - 2,
        tileSize - 2
      );
    });

    // HUD
    ctx.fillStyle = "#fff";
    ctx.font = "16px Arial";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("Score: " + score, 8, 6);
    ctx.fillText("P: Pause", 8, 26);

    // Game over overlay
    if (gameOver) {
      ctx.fillStyle = "rgba(0,0,0,0.7)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = "#fff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "28px Arial";
      ctx.fillText("Game Over", canvas.width / 2, canvas.height / 2 - 20);
      ctx.font = "16px Arial";
      ctx.fillText(
        "Press SPACE to restart",
        canvas.width / 2,
        canvas.height / 2 + 10
      );
      return;
    }

    // Pause menu overlay
    if (paused) {
      ctx.fillStyle = "rgba(0,0,0,0.7)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = "#fff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "28px Arial";
      ctx.fillText("Paused", canvas.width / 2, canvas.height / 2 - 20);
      ctx.font = "16px Arial";
      ctx.fillText(
        "Press P or ESC to resume",
        canvas.width / 2,
        canvas.height / 2 + 10
      );
    }
  }

  function loop(timestamp) {
    if (timestamp - lastTime > speedMs) {
      update();
      lastTime = timestamp;
    }
    draw();
    requestAnimationFrame(loop);
  }

  requestAnimationFrame(loop);
})();