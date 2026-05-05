# envault

> Lightweight .env file manager with per-project secret encryption and team sharing support.

---

## Installation

```bash
pip install envault
```

Or with pipx for global CLI access:

```bash
pipx install envault
```

---

## Usage

Initialize envault in your project directory:

```bash
envault init
```

Add and encrypt a secret:

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"
```

Load secrets into your environment:

```bash
envault run -- python app.py
```

Export secrets for team sharing:

```bash
envault export --output .env.vault
```

Import shared secrets:

```bash
envault import .env.vault
```

In Python:

```python
import envault

envault.load()  # Decrypts and loads secrets into os.environ

import os
print(os.getenv("DATABASE_URL"))
```

---

## License

This project is licensed under the [MIT License](LICENSE).