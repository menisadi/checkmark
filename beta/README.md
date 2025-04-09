# checkmarks

**checkmarks** is a CLI tool for parsing Markdown task lists (`- [ ] Task` or `- [x] Task`) and tracking progress across multiple files. It supports:

- Parsing individual Markdown files for tasks  
- Maintaining a dashboard of “tracked” files  
- Displaying progress in a plain text format or (optionally) using [Rich](https://github.com/Textualize/rich) for nicer output  
- Scanning a directory for Markdown files that contain tasks  
- Exporting a progress overview to an HTML file  

## Installation

Install **checkmarks** directly from [PyPI](https://pypi.org/project/checkmarks/):

```bash
pip install checkmarks
```

After installation, you should have a `checkmarks` command available in your terminal.

## Usage

```
checkmarks - A tool to parse Markdown task lists and display progress.

Usage:
  checkmarks                 # No arguments => Show the dashboard (if any files are tracked)
  checkmarks file.md         # Single markdown file => Parse tasks in that file
  checkmarks parse file.md
  checkmarks add file.md
  checkmarks remove file.md
  checkmarks dashboard [--table | --progress]
  checkmarks export /path/to/output.html
  checkmarks scan /path/to/directory
```

### Subcommands and Features

1. **`checkmarks parse file.md`**  
   Parse a single Markdown file and show the number of tasks plus a progress bar.

2. **`checkmarks add file.md`**  
   Add a file to the "tracked" list in the dashboard configuration (saved in `~/.checkmarks_config.json`).

3. **`checkmarks remove file.md`**  
   Remove a file from the "tracked" list.

4. **`checkmarks dashboard [--table | --progress]`**  
   Display the dashboard of all tracked Markdown files.  
   - No flags: Show simple text-based progress bars  
   - `--table`: Display a Rich table (requires the `rich` library)  
   - `--progress`: Display animated progress bars (requires `rich`)

5. **`checkmarks export /path/to/output.html`**  
   Export the current dashboard to an HTML file showing each file’s progress.

6. **`checkmarks scan /path/to/directory`**  
   Recursively scan a directory for Markdown files containing tasks, then interactively choose which to add to the dashboard.

### Special Behavior

- **No arguments**: `checkmarks` with no arguments automatically shows the dashboard (if there are tracked files).  
- **One .md argument**: `checkmarks file.md` will parse that single file directly.  

## Example Workflows

1. **Track a new project file**  
   ```bash
   checkmarks add docs/README-tasks.md
   checkmarks add docs/another-tasks.md
   checkmarks dashboard
   ```
   This will show a basic text-based progress overview of all tracked files.

2. **Export an HTML Dashboard**  
   ```bash
   checkmarks export progress-report.html
   open progress-report.html
   ```
   Creates an HTML table listing all tasks, how many are completed, and a progress bar.

3. **Use Rich table or Rich progress** (if you have [Rich](https://pypi.org/project/rich/) installed):  
   ```bash
   checkmarks dashboard --table
   ```
   or  
   ```bash
   checkmarks dashboard --progress
   ```

4. **Scan a directory for Markdown**  
   ```bash
   checkmarks scan /path/to/my/markdown/files
   ```

## Configuration File

Tracked files are stored in a simple JSON file at:  
```
~/.checkmarks_config.json
```
This allows the tool to remember which files you’re tracking between runs.

## Rich Integration (Optional)

If you have [Rich](https://github.com/Textualize/rich) installed, you can get nice tables or live progress bars. If it’s not installed, the tool falls back to a plain text output automatically.

To install Rich:
```bash
pip install rich
```
Then run:
```bash
checkmarks dashboard --table
```
or
```bash
checkmarks dashboard --progress
```

## Contributing

Feel free to submit issues or pull requests on the [GitHub repository](https://github.com/menisadi/checkmarks). All contributions are welcome, whether it’s a bug report, a feature suggestion, or a documentation fix.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
