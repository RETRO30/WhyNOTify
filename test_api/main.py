from flask import Flask, jsonify

app = Flask(__name__)

# Полные данные (7 коллекций)
all_collections = [
    {
        "id": 5,
        "title": "Flappy Bird",
        "description": "Welcome to the world of Flappy! Here, you don’t just fly. Fate will hand you your very own bird, and you’ll navigate the challenges together.",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/5/c/logo.png?v=4",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/5/c/cover.png?v=4",
                "type": "cover"
            }
        ],
        "status": "active",
        "badges": [
            "official"
        ]
    },
    {
        "id": 1,
        "title": "DOGS OG",
        "description": "Meet Dogs and get ready to meet your new best friend who’s always got your back (and your snacks)!",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/1/c/logo.png?v=3",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/1/c/cover.png?v=3",
                "type": "cover"
            }
        ],
        "status": "active",
        "badges": [
            "official"
        ]
    },
    {
        "id": 3,
        "title": "Bored Stickers",
        "description": "Apes Together Boring. Stickers for the most famous Apes on the NFT market.",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/3/c/logo.png?v=4",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/3/c/cover.png?v=4",
                "type": "cover"
            }
        ],
        "status": "active",
        "badges": [
            "official"
        ]
    },
    {
        "id": 6,
        "title": "Notcoin Skins",
        "description": "Probably soon",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/6/c/logo.png?v=2",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/6/c/cover.png?v=2",
                "type": "cover"
            }
        ],
        "status": "soon",
        "badges": [
            "official"
        ]
    },
    {
        "id": 4,
        "title": "Blum",
        "description": "In a universe full of possibilities, the stars aligned and gave you these pixelated ones. Unexpected? Absolutely! But all we can do now is roll with these quirky little stars and have some fun!",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/4/c/logo.png?v=2",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/4/c/cover.png?v=2",
                "type": "cover"
            }
        ],
        "status": "active",
        "badges": [
            "official"
        ]
    },
    {
        "id": 2,
        "title": "Pudgy Penguins",
        "description": "Meet your new cuddly companions. Dive in and discover the one that's meant to waddle into your life—because every penguin deserves a home filled with love!",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/2/c/logo.png?v=7",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/2/c/cover.png?v=7",
                "type": "cover"
            }
        ],
        "status": "active",
        "badges": [
            "official"
        ]
    },
    {
        "id": 7,
        "title": "Lost Dogs",
        "description": "Who are these Lost Dogs? They have an NFT collection, a game, a cartoon, and an entire universe… all for fun?",
        "media": [
            {
                "url": "https://cdn.stickerdom.store/7/c/logo.png?v=2",
                "type": "logo"
            },
            {
                "url": "https://cdn.stickerdom.store/7/c/cover.png?v=2",
                "type": "cover"
            }
        ],
        "status": "active",
        "badges": [
            "official"
        ]
    }
]

# Убираем последнюю коллекцию (например, "Lost Dogs") из общего списка
# и будем добавлять её после первого запроса:
missing_collection = all_collections[-1]
collections = all_collections[:-1]

# Флаг, который обозначает, что первый запрос ещё не был выполнен
first_request = True

@app.route("/api/v1/collections", methods=["GET"])
def get_collections():
    global first_request, collections

    # Если это первый запрос — возвращаем список без последней коллекции
    if first_request:
        first_request = False  # Сбрасываем флаг
        return jsonify({"ok": True, "data": collections})
    else:
        # После первого запроса коллекция добавляется в список
        # Если она ещё не добавлена — добавляем
        if not any(item["id"] == missing_collection["id"] for item in collections):
            collections.append(missing_collection)

        return jsonify({"ok": True, "data": collections})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
