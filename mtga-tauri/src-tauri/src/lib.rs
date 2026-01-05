use std::path::PathBuf;

use pyo3::prelude::*;

fn resolve_python_home() -> Option<PathBuf> {
    if let Some(home) = std::env::var_os("PYTHONHOME") {
        return Some(PathBuf::from(home));
    }

    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            let candidate = exe_dir.join("resources").join("pyembed").join("python");
            if candidate.exists() {
                return Some(candidate);
            }
            let mac_candidate = exe_dir.join("Resources").join("pyembed").join("python");
            if mac_candidate.exists() {
                return Some(mac_candidate);
            }
        }
    }

    if let Ok(manifest_dir) = std::env::var("CARGO_MANIFEST_DIR") {
        let candidate = PathBuf::from(manifest_dir).join("pyembed").join("python");
        if candidate.exists() {
            return Some(candidate);
        }
    }

    None
}

fn resolve_python_paths(python_home: &PathBuf) -> Vec<PathBuf> {
    let mut paths = Vec::new();
    let lib = python_home.join("Lib");
    if lib.exists() {
        paths.push(lib.clone());
        let site = lib.join("site-packages");
        if site.exists() {
            paths.push(site);
        }
        return paths;
    }

    let unix_lib = python_home.join("lib");
    if !unix_lib.exists() {
        return paths;
    }
    if let Ok(entries) = std::fs::read_dir(&unix_lib) {
        for entry in entries.flatten() {
            let path = entry.path();
            if !path.is_dir() {
                continue;
            }
            let name = path.file_name().and_then(|value| value.to_str()).unwrap_or("");
            if !name.starts_with("python") {
                continue;
            }
            paths.push(path.clone());
            let site = path.join("site-packages");
            if site.exists() {
                paths.push(site);
            }
        }
    }
    paths
}

fn resolve_env_file(python_home: &PathBuf) -> Option<PathBuf> {
    let windows_candidate = python_home.join("Lib").join(".env");
    if windows_candidate.exists() {
        return Some(windows_candidate);
    }

    let unix_lib = python_home.join("lib");
    if unix_lib.exists() {
        let direct = unix_lib.join(".env");
        if direct.exists() {
            return Some(direct);
        }
        if let Ok(entries) = std::fs::read_dir(&unix_lib) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    let candidate = path.join(".env");
                    if candidate.exists() {
                        return Some(candidate);
                    }
                }
            }
        }
    }

    None
}

fn ensure_python_env() -> Option<PathBuf> {
    let home = resolve_python_home();
    let Some(home_path) = home.as_ref() else {
        return None;
    };

    if std::env::var_os("PYTHONHOME").is_none() {
        std::env::set_var("PYTHONHOME", home_path);
    }

    if std::env::var_os("PYTHONPATH").is_none() {
        let paths = resolve_python_paths(home_path);
        if !paths.is_empty() {
            let separator = if cfg!(windows) { ";" } else { ":" };
            let joined = paths
                .iter()
                .map(|path| path.to_string_lossy())
                .collect::<Vec<_>>()
                .join(separator);
            std::env::set_var("PYTHONPATH", joined);
        }
    }

    if std::env::var_os("MTGA_ENV_FILE").is_none() {
        if let Some(env_file) = resolve_env_file(home_path) {
            std::env::set_var("MTGA_ENV_FILE", env_file);
        }
    }

    Some(home_path.clone())
}

fn build_py_invoke_handler() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let module = PyModule::import(py, "mtga_app")?;
        let handler = module.getattr("get_py_invoke_handler")?.call0()?;
        Ok(handler.unbind())
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    if !cfg!(debug_assertions) && std::env::var("MTGA_RUNTIME").is_err() {
        std::env::set_var("MTGA_RUNTIME", "tauri");
    }

    ensure_python_env();
    pyo3::prepare_freethreaded_python();
    let py_invoke_handler =
        build_py_invoke_handler().expect("Failed to initialize Python invoke handler");

    tauri::Builder::default()
        .plugin(tauri_plugin_pytauri::init(py_invoke_handler))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
