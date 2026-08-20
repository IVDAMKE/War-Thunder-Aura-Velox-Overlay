# Tauri + SvelteKit

This template should help get you started developing with Tauri and SvelteKit in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Svelte](https://marketplace.visualstudio.com/items?itemName=svelte.svelte-vscode) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer).


# REMINDER TO ME
[Top-Level: The Frontend](SvelteKit)
The root of your workspace contains your frontend project, which handles the user interface. Because you chose SvelteKit, these files are specific to building and bundling your web code:

<src/:> This is where you will write your Svelte components, HTML, and CSS to design your app's interface.

<static/:> This folder holds static assets like images, fonts, or raw data files that your web frontend might need.

<svelte-kit/:> A generated folder used internally by SvelteKit during development to process your files.

<package.json > and <package-lock.json:> These files manage your Node.js dependencies, tracking the frontend tools and libraries your project needs (like Vite and the Tauri JS API).

<vite.config.js >and <velte.config.js:> These are configuration files that dictate how Vite (your web bundler) and SvelteKit process your frontend code.

[src-tauri/: The Backend](Rust)
This subdirectory houses the Rust project, which serves as the core engine of your Tauri application.

<src/:> This directory contains your Rust source code. Inside, you will find main.rs, which is the main entry point for the desktop application. You will also find lib.rs, which contains your core Rust logic and acts as the entry point for mobile builds.

<tauri.conf.json:> This is the main configuration file for Tauri. It serves as a marker for the Tauri CLI to locate your Rust project, and it contains essential settings like your application's identifier and development server URLs.

<capabilities/:> This is the default directory where Tauri reads capability files. These JSON files define strict security permissions, allowing you to explicitly declare which backend commands your JavaScript code is allowed to use.

<icons/:> This folder is the default output directory for your application's icons (like .ico for Windows or .png for Linux). These icons are referenced directly inside your tauri.conf.json file.

<Cargo.toml> and <Cargo.lock:> These are the manifest files for Cargo, Rust's built-in package manager. They declare the backend libraries (crates) your Rust code requires.

<build.rs:> This is a Rust build script that is utilized by Tauri's build system during compilation.

<target/:> This generated folder is where Cargo places all of your compiled binary files and build artifacts. When you eventually package your app for release, the final .exe file will be built here.