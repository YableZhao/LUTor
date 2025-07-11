# LUTor 🎨

**LUTor** is a simple and intuitive web-based tool that allows you to transfer the color style from a reference image to your own photos. It's perfect for photographers, designers, and anyone looking to quickly create beautiful "filters" or color grades.

The application also allows you to export the resulting color transformation as a **3D LUT** (`.cube`) for use in video editing software (like DaVinci Resolve, Premiere Pro) or as a **Lightroom Preset** (`.xmp`) for your photo editing workflow.


## Features

-   **🎨 Real-time Color Style Transfer**: Apply the color palette of any image to another.
-   **💪 Adjustable Strength**: Control the intensity of the style transfer.
-   **🖼️ Preset Styles**: Comes with a few built-in styles to get you started.
-   **💾 Export Options**:
    -   Download the stylized image as a high-quality JPEG.
    -   Export a **3D LUT** (`.cube`) file for video color grading.
    -   Export a **Lightroom Preset** (`.xmp`) for your photo workflow.
-   **🌐 Fully Web-Based**: No complex setup, just run the app and open your browser.
-   **⚡ Lightweight & Fast**: No heavy AI models, processing is almost instantaneous.

## How It Works

This tool uses a classic computer vision algorithm called **Histogram Matching**. It analyzes the color distribution (histogram) of the style image and intelligently adjusts the colors of your content image to match that distribution. This technique purely manipulates color and tone, preserving all the details and realism of your original photo.

## Quick Start

### 1. Installation

First, clone this repository and navigate into the directory:

```bash
git clone https://github.com/your-username/lutor.git
cd lutor
```

Next, it's highly recommended to use a Python virtual environment.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it (on macOS/Linux)
source venv/bin/activate

# On Windows, use:
# venv\Scripts\activate
```

Now, install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Running the Application

Once the dependencies are installed, start the web server with this simple command:

```bash
python3 app.py
```

You will see a message in your terminal indicating that the server is running. Now, just open your web browser and go to:

**http://127.0.0.1:5001**

### 3. Using the App

1.  **Upload Content Image**: Drag and drop your photo into the left-hand panel.
2.  **Upload Style Image**: Drag and drop an image with the color style you like into the middle panel, or select one of the presets.
3.  **Adjust & See**: The result will appear instantly on the right. Use the slider to adjust the style strength.
4.  **Export**: Download your creation as a stylized image, a `.cube` file, or an `.xmp` preset.

## To-Do / Future Ideas

-   [ ] Add more built-in preset styles.
-   [ ] Allow users to save their own styles in the browser's local storage.
-   [ ] Improve the UI/UX.
-   [ ] Batch processing for multiple images.

## Contributing

Contributions are welcome! If you have ideas for new features or improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
