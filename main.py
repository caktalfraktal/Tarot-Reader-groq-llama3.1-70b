import tkinter as tk
from PIL import Image, ImageTk
import os
import random
import threading

from tarot_deck import tarot_deck

# Try to import Groq and set up the client if available
try:
    from groq import Groq
    # Set your Groq API key
    groq_api_key = 'REPLACE_THIS_WITH_YOUR_GROQ_API_KEY'  # Replace with your actual Groq API key (within the apostrophes)

    client = Groq(
        api_key=groq_api_key,
    )
    groq_available = True
except ImportError:
    groq_available = False
    client = None

def generate_tarot_reading(cards, query):
    # Check if Groq is available and the client is initialized
    if not groq_available or client is None:
        return None  # No reading generated

    # Include the user's query in the prompt without referencing "the querent"
    if query.strip():
        query_text = f"The following question is considered: '{query.strip()}'."
    else:
        query_text = "No specific question is provided."

    # Determine the spread type based on the number of cards
    num_cards = len(cards)
    if num_cards == 1:
        # Build the prompt for a one-card reading
        prompt = f"""
{query_text}

Provide a reading based on the following card:

{cards[0]['name']}.

Interpret the card without referencing the client directly. Do not use 'you', 'your', or 'the querent' in the reading. Do not assign specific positions or standard meanings to the card. Do not include any introductory phrases or acknowledgements. Start the reading directly and ensure it relates to the question if one is provided.
"""
    elif num_cards == 3:
        # Build the prompt for a three-card reading
        card_list = "\n".join([f"Card {i+1}: {cards[i]['name']}" for i in range(3)])
        prompt = f"""
{query_text}

Provide a reading based on the following cards:

{card_list}

Provide an interpretation for each card individually, without assigning specific positions or standard meanings to each card, **and then give an overall interpretation at the end that ties all the insights together**. Do not reference the client directly. Do not use 'you', 'your', or 'the querent' in the reading. Do not include any introductory phrases or acknowledgements. Start the reading directly and ensure it relates to the question if one is provided.
"""
    elif num_cards == 10:
        # Positions for Celtic Cross
        positions = [
            "Present Situation (1)",
            "Influences or Challenges (2)",
            "Distant Past (3)",
            "Recent Past (4)",
            "Best Outcome (5)",
            "Immediate Future (6)",
            "Advice (7)",
            "Environment (8)",
            "Hopes or Fears (9)",
            "Potential Outcome (10)"
        ]
        card_positions = "\n".join([f"{positions[i]}: {cards[i]['name']}" for i in range(10)])
        prompt = f"""
{query_text}

Provide a Celtic Cross reading based on the following cards and their positions:

{card_positions}

Associate each card with its position using the exact position names provided. Provide an interpretation for each card in its position, and then give an overall interpretation at the end that ties all the insights together. Do not reference the client directly. Do not use 'you', 'your', or 'the querent' in the reading. Do not change the position names or numbering. Do not include any introductory phrases or acknowledgements. Start the reading directly and ensure it relates to the question if one is provided.
"""
    else:
        # For other spreads
        card_names = ', '.join([card['name'] for card in cards])
        prompt = f"""
{query_text}

Provide a reading based on the following cards:

{card_names}.

Interpret the cards as appropriate for a {num_cards}-card spread, without assigning specific positions or standard meanings to each card. Do not reference the client directly. Do not use 'you', 'your', or 'the querent' in the reading. Do not include any introductory phrases or acknowledgements. Start the reading directly and ensure it relates to the question if one is provided.
"""
    try:
        # Use the Groq API to generate the completion
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ],
            model="llama-3.1-70b-versatile",  # Replace with your desired Llama model
            max_tokens=5000,
            temperature=0.6 ## Adjusts how "creative" the readings are.
        )
        reading = chat_completion.choices[0].message.content.strip()
        return reading
    except Exception as e:
        # Do not return error messages
        return None  # Simply return None if an error occurs

def draw_cards(num_cards):
    deck = tarot_deck.copy()
    random.SystemRandom().shuffle(deck)
    drawn_cards = deck[:num_cards]
    return drawn_cards

def draw_celtic_cross(canvas_frame, text_box, query_entry):
    for widget in canvas_frame.winfo_children():
        widget.destroy()
    cards = draw_cards(10)
    images = []
    for i, card in enumerate(cards):
        image_path = os.path.join(os.path.dirname(__file__), card['image'])
        pil_image = Image.open(image_path)
        if i == 1:
            pil_image = pil_image.rotate(90, expand=True)
        images.append(pil_image)
    canvas = tk.Canvas(canvas_frame)
    canvas.pack(fill="both", expand=True)
    canvas.images = images
    canvas.bind("<Configure>", lambda event: redraw_celtic_cross(canvas, images))
    redraw_celtic_cross(canvas, images)
    positional_names = [
        "Present Situation (1)",
        "Influences or Challenges (2)",
        "Distant Past (3)",
        "Recent Past (4)",
        "Best Outcome (5)",
        "Immediate Future (6)",
        "Advice (7)",
        "Environment (8)",
        "Hopes or Fears (9)",
        "Potential Outcome (10)"
    ]
    card_meanings = "\n".join([f"{positional_names[i]}:\n{cards[i]['name']} - {cards[i]['meaning']}\n" for i in range(10)])
    text_box.config(state="normal")
    text_box.delete("1.0", tk.END)
    text_box.insert("1.0", card_meanings)
    text_box.config(state="disabled")

    # Get the user's query
    user_query = query_entry.get()

    # Generate and display the tarot reading in a separate thread
    def update_reading():
        reading = generate_tarot_reading(cards, user_query)
        if reading:
            # Schedule the GUI update in the main thread
            text_box.after(0, display_reading, reading)

    def display_reading(reading):
        if reading:
            text_box.config(state="normal")
            text_box.insert(tk.END, f"\nTarot Reading:\n{reading}")
            text_box.config(state="disabled")

    threading.Thread(target=update_reading, daemon=True).start()

def redraw_celtic_cross(canvas, images):
    # [Existing code for redrawing the Celtic Cross layout]
    canvas.delete("all")
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    if canvas_width <= 0 or canvas_height <= 0:
        return
    card_original_width = images[0].width
    card_original_height = images[0].height
    spacing = 20
    horizontal_spacing = 125
    vertical_spacing_7_10 = -24
    extra_horizontal_spacing_4_6 = 60
    extra_horizontal_offset_7_10 = 30
    padding_left = 55
    padding_right = 35

    total_width = (
        4 * card_original_width
        + 3 * horizontal_spacing
        + 3 * extra_horizontal_spacing_4_6
        + extra_horizontal_offset_7_10
        + padding_left
        + padding_right
    )
    total_height = card_original_height * 4 + (-24 * 3)
    scaling_x = canvas_width / total_width
    scaling_y = canvas_height / total_height
    scaling = min(scaling_x, scaling_y, 1)
    spacing *= scaling
    horizontal_spacing *= scaling
    vertical_spacing_7_10 *= scaling
    extra_horizontal_spacing_4_6 *= scaling
    extra_horizontal_offset_7_10 *= scaling
    padding_left *= scaling
    padding_right *= scaling
    resized_images = []
    for i, pil_image in enumerate(images):
        img = pil_image.copy()
        new_width = max(int(img.width * scaling), 1)
        new_height = max(int(img.height * scaling), 1)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        resized_image = ImageTk.PhotoImage(img)
        resized_images.append(resized_image)
    card_width = resized_images[0].width()
    card_height = resized_images[0].height()
    total_width = (
        4 * card_width
        + 3 * horizontal_spacing
        + 3 * extra_horizontal_spacing_4_6
        + extra_horizontal_offset_7_10
        + padding_left
        + padding_right
    )
    leftmost_x = (canvas_width - total_width) / 2 + padding_left
    center_x = leftmost_x + card_width + horizontal_spacing + extra_horizontal_spacing_4_6
    center_y = canvas_height / 2 - card_height / 2
    positions = [
        (center_x, center_y),
        (
            center_x + (card_width - resized_images[1].width()) / 2,
            center_y + (card_height - resized_images[1].height()) / 2,
        ),
        (center_x, center_y + card_height + spacing),
        (
            center_x - card_width - horizontal_spacing - extra_horizontal_spacing_4_6,
            center_y,
        ),
        (center_x, center_y - card_height - spacing),
        (
            center_x + card_width + horizontal_spacing + extra_horizontal_spacing_4_6,
            center_y,
        ),
    ]
    x_offset = (
        center_x
        + 2 * (card_width + horizontal_spacing)
        + extra_horizontal_offset_7_10
        + 2 * extra_horizontal_spacing_4_6
    )
    y_offset = center_y + 1.5 * (card_height + vertical_spacing_7_10)
    for i in range(6, 10):
        positions.append(
            (x_offset, y_offset - (card_height + vertical_spacing_7_10) * (i - 6))
        )
    for i, (x, y) in enumerate(positions):
        canvas.create_image(x, y, image=resized_images[i], anchor='nw')
    canvas.images = resized_images

def draw_one_card(canvas_frame, text_box, query_entry):
    for widget in canvas_frame.winfo_children():
        widget.destroy()
    cards = draw_cards(1)
    images = []
    card = cards[0]
    image_path = os.path.join(os.path.dirname(__file__), card['image'])
    pil_image = Image.open(image_path)
    images.append(pil_image)
    canvas = tk.Canvas(canvas_frame)
    canvas.pack(fill="both", expand=True)
    canvas.images = images
    canvas.bind("<Configure>", lambda event: redraw_one_card(canvas, images))
    redraw_one_card(canvas, images)
    card_meanings = f"Card:\n{cards[0]['name']} - {cards[0]['meaning']}\n"
    text_box.config(state="normal")
    text_box.delete("1.0", tk.END)
    text_box.insert("1.0", card_meanings)
    text_box.config(state="disabled")

    # Get the user's query
    user_query = query_entry.get()

    # Generate and display the tarot reading in a separate thread
    def update_reading():
        reading = generate_tarot_reading(cards, user_query)
        if reading:
            text_box.after(0, display_reading, reading)

    def display_reading(reading):
        if reading:
            text_box.config(state="normal")
            text_box.insert(tk.END, f"\nTarot Reading:\n{reading}")
            text_box.config(state="disabled")

    threading.Thread(target=update_reading, daemon=True).start()

def redraw_one_card(canvas, images):
    canvas.delete("all")
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    if canvas_width <= 0 or canvas_height <= 0:
        return
    padding_left = 32
    padding_right = 22
    available_width = canvas_width - padding_left - padding_right
    img = images[0]
    scaling = min(
        available_width / img.width,
        canvas_height / img.height,
        1
    )
    if scaling <= 0:
        scaling = 1
    new_width = max(int(img.width * scaling), 1)
    new_height = max(int(img.height * scaling), 1)
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
    resized_image = ImageTk.PhotoImage(img_resized)
    image_x = padding_left + (available_width - resized_image.width()) // 2
    image_y = (canvas_height - resized_image.height()) // 2
    canvas.create_image(image_x, image_y, image=resized_image, anchor='nw')
    canvas.images = [resized_image]

def draw_three_cards(canvas_frame, text_box, query_entry):
    for widget in canvas_frame.winfo_children():
        widget.destroy()
    cards = draw_cards(3)
    images = []
    for card in cards:
        image_path = os.path.join(os.path.dirname(__file__), card['image'])
        pil_image = Image.open(image_path)
        images.append(pil_image)
    canvas = tk.Canvas(canvas_frame)
    canvas.pack(fill="both", expand=True)
    canvas.images = images
    canvas.bind("<Configure>", lambda event: redraw_three_cards(canvas, images))
    redraw_three_cards(canvas, images)
    card_names = [card['name'] for card in cards]
    card_meanings = "\n".join([f"Card {i+1}:\n{card_names[i]} - {cards[i]['meaning']}\n" for i in range(3)])
    text_box.config(state="normal")
    text_box.delete("1.0", tk.END)
    text_box.insert("1.0", card_meanings)
    text_box.config(state="disabled")

    # Get the user's query
    user_query = query_entry.get()

    # Generate and display the tarot reading in a separate thread
    def update_reading():
        reading = generate_tarot_reading(cards, user_query)
        if reading:
            # Schedule the GUI update in the main thread
            text_box.after(0, display_reading, reading)

    def display_reading(reading):
        if reading:
            text_box.config(state="normal")
            text_box.insert(tk.END, f"\nTarot Reading:\n{reading}")
            text_box.config(state="disabled")

    threading.Thread(target=update_reading, daemon=True).start()

def redraw_three_cards(canvas, images):
    canvas.delete("all")
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    if canvas_width <= 0 or canvas_height <= 0:
        return
    img_width = images[0].width
    img_height = images[0].height
    spacing = 25
    padding_left = 32
    padding_right = 22
    total_width = padding_left + img_width * 3 + spacing * 2 + padding_right
    scaling = min(
        canvas_width / total_width,
        canvas_height / img_height
    )
    scaling = min(scaling, 1)
    if scaling <= 0:
        scaling = 1
    horizontal_spacing = spacing * scaling
    padding_left_scaled = padding_left * scaling
    padding_right_scaled = padding_right * scaling
    resized_images = []
    for img in images:
        new_width = max(int(img.width * scaling), 1)
        new_height = max(int(img.height * scaling), 1)
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        resized_image = ImageTk.PhotoImage(img_resized)
        resized_images.append(resized_image)
    card_width = resized_images[0].width()
    card_height = resized_images[0].height()
    total_width = padding_left_scaled + card_width * 3 + horizontal_spacing * 2 + padding_right_scaled
    start_x = (canvas_width - total_width) // 2 + padding_left_scaled
    center_y = canvas_height // 2 - card_height // 2
    positions = [
        (start_x, center_y),
        (start_x + card_width + horizontal_spacing, center_y),
        (start_x + 2 * (card_width + horizontal_spacing), center_y)
    ]
    for i, (x, y) in enumerate(positions):
        canvas.create_image(x, y, image=resized_images[i], anchor='nw')
    canvas.images = resized_images

def setup_main_gui(root, spread_type=None):
    sample_card_path = os.path.join(os.path.dirname(__file__), tarot_deck[0]['image'])
    sample_card_image = Image.open(sample_card_path)
    card_width, card_height = sample_card_image.size
    spacing = 25
    padding_left = 30
    padding_right = 30
    total_width = padding_left + card_width * 3 + spacing * 2 + padding_right
    window_width = total_width + 280
    window_height = card_height + 175
    root.geometry(f"{int(window_width)}x{int(window_height)}")
    root.resizable(True, True)
    content_frame = tk.Frame(root)
    content_frame.pack(fill="both", expand=True)
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=3)
    content_frame.grid_columnconfigure(1, weight=1)
    canvas_frame = tk.Frame(content_frame)
    canvas_frame.grid(row=0, column=0, sticky="nsew")
    right_frame = tk.Frame(content_frame, width=245)
    right_frame.grid(row=0, column=1, sticky="nsew")
    right_frame.grid_propagate(False)

    # Adjust grid weights for right_frame
    right_frame.grid_rowconfigure(1, weight=0)
    right_frame.grid_rowconfigure(2, weight=1)  # Text frame
    right_frame.grid_rowconfigure(3, weight=0)  # Buttons frame
    right_frame.grid_columnconfigure(0, weight=1)

    # Query input field
    query_label = tk.Label(right_frame, text="Enter your query:")
    query_label.grid(row=0, column=0, padx=6, pady=2, sticky="w")

    query_entry = tk.Entry(right_frame, width=30)
    query_entry.grid(row=1, column=0, padx=10, pady=4, sticky="we")

    text_frame = tk.Frame(right_frame)
    text_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)
    text_box = tk.Text(text_frame, wrap="word", font=("Courier New", 10), width=37)
    text_box.grid(row=0, column=0, sticky="nsew")
    scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=text_box.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_box.config(yscrollcommand=scrollbar.set)
    text_box.config(state="disabled")

    buttons_frame = tk.Frame(right_frame)
    buttons_frame.grid(row=3, column=0, padx=5, pady=(1, 10), sticky="n")
    draw_one_card_button = tk.Button(
        buttons_frame,
        text="Draw One Card",
        width=20,
        command=lambda: draw_one_card(canvas_frame, text_box, query_entry)
    )
    draw_one_card_button.pack(pady=3)
    draw_three_cards_button = tk.Button(
        buttons_frame,
        text="Draw Three Cards",
        width=20,
        command=lambda: draw_three_cards(canvas_frame, text_box, query_entry)
    )
    draw_three_cards_button.pack(pady=3)
    draw_celtic_button = tk.Button(
        buttons_frame,
        text="Draw Celtic Cross",
        width=20,
        command=lambda: draw_celtic_cross(canvas_frame, text_box, query_entry)
    )
    draw_celtic_button.pack(pady=3)
    if spread_type is None:
        add_placeholder(canvas_frame)
    else:
        if spread_type == "celtic":
            draw_celtic_cross(canvas_frame, text_box, query_entry)
        elif spread_type == "one":
            draw_one_card(canvas_frame, text_box, query_entry)
        elif spread_type == "three":
            draw_three_cards(canvas_frame, text_box, query_entry)

def add_placeholder(canvas_frame):
    try:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        image_path = os.path.join(os.path.dirname(__file__), "back.gif")
        pil_image = Image.open(image_path)
        canvas = tk.Canvas(canvas_frame)
        canvas.pack(fill="both", expand=True)
        canvas.placeholder_image = pil_image
        canvas.bind("<Configure>", lambda event: redraw_placeholder(canvas, pil_image))
        redraw_placeholder(canvas, pil_image)
    except Exception as e:
        print(f"Error loading placeholder image: {e}")

def redraw_placeholder(canvas, pil_image):
    canvas.delete("all")
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    if canvas_width <= 0 or canvas_height <= 0:
        return
    padding_left = 32
    padding_right = 22
    available_width = canvas_width - padding_left - padding_right
    scaling = min(
        available_width / pil_image.width,
        canvas_height / pil_image.height,
        1
    )
    if scaling <= 0:
        scaling = 1
    new_width = max(int(pil_image.width * scaling), 1)
    new_height = max(int(pil_image.height * scaling), 1)
    img = pil_image.resize((new_width, new_height), Image.LANCZOS)
    resized_image = ImageTk.PhotoImage(img)
    image_x = padding_left + (available_width - resized_image.width()) // 2
    image_y = (canvas_height - resized_image.height()) // 2
    canvas.create_image(image_x, image_y, image=resized_image, anchor='nw')
    canvas.placeholder_image = resized_image

def main():
    root = tk.Tk()
    root.title("Tarot Reader")
    root.resizable(True, True)
    setup_main_gui(root, spread_type=None)
    root.mainloop()

if __name__ == "__main__":
    main()