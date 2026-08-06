import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "priconne_unhash.py"
SPEC = importlib.util.spec_from_file_location("priconne_unhash", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_database(path: Path, table_name: str, column_names: tuple[str, str]) -> None:
    with closing(sqlite3.connect(path)) as db:
        db.execute(
            f'CREATE TABLE "{table_name}" ('
            f'"{column_names[0]}" INTEGER PRIMARY KEY, '
            f'"{column_names[1]}" TEXT NOT NULL)'
        )
        db.executemany(
            f'INSERT INTO "{table_name}" VALUES (?, ?)',
            [(1, "one"), (2, "two"), (3, "three")],
        )
        db.commit()


class UnhashTests(unittest.TestCase):
    def test_prepare_jp_database_keeps_canonical_second_mirror(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.db"
            output = root / "canonical.db"
            with closing(sqlite3.connect(source)) as db:
                for name, value in (
                    ("v1_" + "a" * 64, "old-a"),
                    ("v1_" + "b" * 64, "old-b"),
                    ("v1_" + "c" * 64, "new-a"),
                    ("v1_" + "d" * 64, "new-b"),
                ):
                    db.execute(f'CREATE TABLE "{name}" (id INTEGER PRIMARY KEY, value TEXT)')
                    db.execute(f'INSERT INTO "{name}" VALUES (1, ?)', (value,))
                db.commit()

            stats = MODULE.prepare_jp_canonical_database(source, output)

            self.assertEqual(stats["mirrored_schema"], 1)
            self.assertEqual(stats["discarded_tables"], 2)
            self.assertEqual(
                [table.name for table in MODULE.inspect_database(output)],
                ["v1_" + "c" * 64, "v1_" + "d" * 64],
            )

    def test_same_version_positional_match_recovers_repeated_zero_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.db"
            target = root / "target.db"
            with closing(sqlite3.connect(reference)) as db:
                db.execute(
                    'CREATE TABLE skill_data (skill_id INTEGER PRIMARY KEY, '
                    'action_19 INTEGER, action_20 INTEGER)'
                )
                db.executemany(
                    'INSERT INTO skill_data VALUES (?, 0, 0)', [(1,), (2,), (3,)]
                )
                db.commit()
            table_hash = "v1_" + "e" * 64
            column_hashes = [character * 64 for character in "fgh"]
            with closing(sqlite3.connect(target)) as db:
                db.execute(
                    f'CREATE TABLE "{table_hash}" ('
                    f'"{column_hashes[0]}" INTEGER PRIMARY KEY, '
                    f'"{column_hashes[1]}" INTEGER, "{column_hashes[2]}" INTEGER)'
                )
                db.executemany(
                    f'INSERT INTO "{table_hash}" VALUES (?, 0, 0)', [(1,), (2,), (3,)]
                )
                db.commit()

            transferred = MODULE.match_columns(
                reference,
                MODULE.inspect_database(reference)[0],
                target,
                MODULE.inspect_database(target)[0],
                prefer_position=True,
            )

            self.assertEqual(
                list(transferred.values()), ["skill_id", "action_19", "action_20"]
            )

    def test_lower_priority_reference_fills_unmatched_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preferred = root / "preferred.db"
            fallback = root / "fallback.db"
            target = root / "target.db"
            table_hash = "v1_" + "1" * 64
            columns = [character * 64 for character in "234"]
            for path, name_value, name_column in (
                (preferred, "Hiyori", "unit_name_jp"),
                (fallback, "ヒヨリ", "unit_name"),
            ):
                with closing(sqlite3.connect(path)) as db:
                    db.execute(
                        f'CREATE TABLE unit_data (unit_id INTEGER PRIMARY KEY, '
                        f'{name_column} TEXT, rarity INTEGER)'
                    )
                    db.executemany(
                        'INSERT INTO unit_data VALUES (?, ?, ?)',
                        [(1, name_value, 1), (2, name_value, 2), (3, name_value, 3)],
                    )
                    db.commit()
            with closing(sqlite3.connect(target)) as db:
                db.execute(
                    f'CREATE TABLE "{table_hash}" ('
                    f'"{columns[0]}" INTEGER PRIMARY KEY, '
                    f'"{columns[1]}" TEXT, "{columns[2]}" INTEGER)'
                )
                db.executemany(
                    f'INSERT INTO "{table_hash}" VALUES (?, ?, ?)',
                    [(1, "ヒヨリ", 1), (2, "ヒヨリ", 2), (3, "ヒヨリ", 3)],
                )
                db.commit()

            mapping = MODULE.resolve_mapping(
                target,
                [],
                [("roboninon", preferred, 260), ("previous", fallback, 130)],
            )

            recovered = mapping["tables"][table_hash]["columns"]
            self.assertEqual(recovered[columns[1]], "unit_name")
            self.assertEqual(recovered[columns[2]], "rarity")

    def test_previous_mapping_cannot_downgrade_same_version_name_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pcr_tool = root / "pcr_tool.db"
            roboninon = root / "roboninon.db"
            previous_raw = root / "previous_raw.db"
            previous_mapping = root / "mapping.json"
            target = root / "target.db"
            table_hash = "v1_" + "5" * 64
            old_table_hash = "v1_" + "6" * 64
            target_columns = [character * 64 for character in "789"]
            old_columns = [character * 64 for character in "abc"]

            for path, table, columns in (
                (target, table_hash, target_columns),
                (previous_raw, old_table_hash, old_columns),
            ):
                with closing(sqlite3.connect(path)) as db:
                    db.execute(
                        f'CREATE TABLE "{table}" ('
                        f'"{columns[0]}" INTEGER PRIMARY KEY, '
                        f'"{columns[1]}" TEXT, "{columns[2]}" INTEGER)'
                    )
                    db.executemany(
                        f'INSERT INTO "{table}" VALUES (?, ?, ?)',
                        [(1, "ヒヨリ", 1), (2, "ヒヨリ", 2), (3, "ヒヨリ", 3)],
                    )
                    db.commit()
            for path, name_column in (
                (pcr_tool, "unit_name"),
                (roboninon, "unit_name_jp"),
            ):
                with closing(sqlite3.connect(path)) as db:
                    db.execute(
                        f'CREATE TABLE unit_data (unit_id INTEGER PRIMARY KEY, '
                        f'{name_column} TEXT, rarity INTEGER)'
                    )
                    db.executemany(
                        'INSERT INTO unit_data VALUES (?, ?, ?)',
                        [(1, "ヒヨリ", 1), (2, "ヒヨリ", 2), (3, "ヒヨリ", 3)],
                    )
                    db.commit()
            previous_mapping.write_text(
                json.dumps(
                    {
                        "tables": {
                            old_table_hash: {
                                "name": "unit_data",
                                "columns": dict(
                                    zip(old_columns, ["unit_id", "unit_name", "rarity"])
                                ),
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            mapping = MODULE.resolve_mapping(
                target,
                [],
                [("pcr-tool", pcr_tool, 320), ("roboninon", roboninon, 260)],
                previous_db=previous_raw,
                previous_mapping_path=previous_mapping,
            )

            recovered = mapping["tables"][table_hash]["columns"]
            self.assertEqual(recovered[target_columns[1]], "unit_name")

    def test_cn_headers_and_discovery_are_ios_only(self):
        headers = MODULE.cn_request_headers("11.7.2")
        self.assertEqual(headers["PLATFORM"], "1")
        self.assertEqual(headers["PLATFORM-ID"], "1")
        self.assertEqual(headers["DEVICE"], "1")

        observed = []

        def probe(version, resources, platforms=("iOS",)):
            observed.append((version, tuple(resources), platforms))
            if version != MODULE.CN_IOS_BASELINE_VERSION:
                return None
            return {
                "version": version,
                "platform": "iOS",
                "cdn": "https://ios.example/",
                "path": "a/masterdata_master.unity3d",
                "md5": "a" * 32,
                "storage_hash": "b" * 16,
                "size": 123,
            }

        with (
            patch.object(MODULE, "fetch_cn_app_version", return_value="11.7.2"),
            patch.object(
                MODULE,
                "fetch_cn_status",
                return_value=(
                    {"manifest_ver": "202607312055", "resource": ["ios.example/"]},
                    "11.7.2",
                ),
            ),
            patch.object(MODULE, "probe_cn_build", side_effect=probe),
        ):
            build, sources, _ = MODULE.discover_cn_build()

        self.assertEqual(build["version"], MODULE.CN_IOS_BASELINE_VERSION)
        self.assertEqual(set(sources), {"official-ios", "ios-baseline"})
        self.assertTrue(observed)
        self.assertTrue(all(platforms == ("iOS",) for _, _, platforms in observed))

    def test_cn_manifest_uses_storage_hash_when_present(self):
        current = MODULE.parse_cn_asset_line(
            "a/masterdata_master.unity3d,"
            "92f78a332512683593ef24406ad428db,"
            "3f33b27b9f8294ee,tutorial2,13292264,"
        )
        self.assertEqual(current["md5"], "92f78a332512683593ef24406ad428db")
        self.assertEqual(current["storage_hash"], "3f33b27b9f8294ee")
        self.assertEqual(current["size"], 13292264)

        legacy = MODULE.parse_cn_asset_line(
            "a/masterdata_master.unity3d,"
            "92f78a332512683593ef24406ad428db,tutorial2,13292264,"
        )
        self.assertEqual(legacy["storage_hash"], legacy["md5"])

    def test_jp_discovery_uses_only_official_ios_candidates(self):
        observed = []

        def probe(version, cdn, version_width=0):
            observed.append((version, cdn, version_width))
            if version in (10070110, 10070120):
                return {
                    "version": str(version),
                    "platform": "iOS",
                    "cdn": cdn,
                    "path": "a/masterdata_master_0003.cdb",
                    "md5": "a" * 32,
                    "storage_hash": "b" * 16,
                    "size": 123,
                }
            return None

        with patch.object(MODULE, "probe_ios_build", side_effect=probe):
            build = MODULE.discover_jp_build({"version": 10070110})

        self.assertEqual(build["version"], "10070120")
        self.assertTrue(observed)
        self.assertTrue(all(cdn == MODULE.JP_IOS_CDN for _, cdn, _ in observed))

    def test_reference_names_are_transferred_and_applied(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.db"
            target = root / "target.db"
            output = root / "output.db"
            rainbow = root / "rainbow.json"
            make_database(reference, "unit_data", ("unit_id", "name"))
            make_database(target, "v1_" + "a" * 64, ("b" * 64, "c" * 64))
            rainbow.write_text("{}", encoding="utf-8")

            mapping = MODULE.resolve_mapping(
                target,
                rainbow,
                [("test", reference, 100)],
            )
            self.assertEqual(mapping["summary"]["tables_mapped"], 1)
            self.assertEqual(mapping["summary"]["columns_mapped"], 2)

            result = MODULE.deobfuscate_database(target, output, mapping)
            self.assertEqual(result["integrity_check"], "ok")
            with closing(sqlite3.connect(output)) as db:
                columns = [row[1] for row in db.execute('PRAGMA table_info("unit_data")')]
                self.assertEqual(columns, ["unit_id", "name"])

    def test_higher_priority_reference_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preferred = root / "preferred.db"
            previous = root / "previous.db"
            target = root / "target.db"
            make_database(preferred, "preferred_name", ("id", "name"))
            make_database(previous, "previous_name", ("id", "name"))
            make_database(target, "v1_" + "a" * 64, ("b" * 64, "c" * 64))

            mapping = MODULE.resolve_mapping(
                target,
                [],
                [
                    ("roboninon", preferred, 260),
                    ("jp-previous-readable", previous, 130),
                ],
            )

            resolved = mapping["tables"]["v1_" + "a" * 64]
            self.assertEqual(resolved["name"], "preferred_name")
            self.assertEqual(resolved["sources"], ["roboninon"])

    def test_decrypt_jp_cdb_invokes_coneshell_and_validates_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "master.cdb"
            destination = root / "master.db"
            executable = root / "Coneshell_call.exe"
            source.write_bytes(b"encrypted")
            executable.write_bytes(b"test")

            def fake_run(command, **kwargs):
                make_database(
                    Path(command[-1]),
                    "v1_" + "d" * 64,
                    ("e" * 64, "f" * 64),
                )
                return type(
                    "Result",
                    (),
                    {"returncode": 0, "stdout": "", "stderr": ""},
                )()

            with (
                patch.object(MODULE.os, "name", "nt"),
                patch.object(MODULE.subprocess, "run", side_effect=fake_run) as run,
            ):
                stats = MODULE.decrypt_jp_cdb(source, destination, executable)

            self.assertTrue(destination.exists())
            self.assertEqual(stats["tables"], 1)
            command = run.call_args.args[0]
            self.assertEqual(command[1], "-cdb")

    def test_rainbow_direct_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table_hash = "v1_" + "d" * 64
            column_hash = "e" * 64
            target = root / "target.db"
            output = root / "output.db"
            mapping_path = root / "rainbow.json"
            with closing(sqlite3.connect(target)) as db:
                db.execute(
                    f'CREATE TABLE "{table_hash}" ("{column_hash}" INTEGER PRIMARY KEY)'
                )
                db.commit()
            mapping_path.write_text(
                json.dumps(
                    {
                        table_hash: {
                            column_hash: "unit_id",
                            "--table_name": "unit_data",
                        }
                    }
                ),
                encoding="utf-8",
            )
            mapping = MODULE.resolve_mapping(target, mapping_path, [])
            MODULE.deobfuscate_database(target, output, mapping)
            with closing(sqlite3.connect(output)) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchone()[0],
                    "unit_data",
                )

    def test_first_rainbow_file_has_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table_hash = "v1_" + "7" * 64
            column_hash = "8" * 64
            target = root / "target.db"
            primary = root / "rainbow_tw.json"
            fallback = root / "rainbow_old.json"
            with closing(sqlite3.connect(target)) as db:
                db.execute(
                    f'CREATE TABLE "{table_hash}" ("{column_hash}" INTEGER)'
                )
                db.commit()
            primary.write_text(
                json.dumps(
                    {
                        table_hash: {
                            column_hash: "primary_id",
                            "--table_name": "primary_table",
                        }
                    }
                ),
                encoding="utf-8",
            )
            fallback.write_text(
                json.dumps(
                    {
                        table_hash: {
                            column_hash: "fallback_id",
                            "--table_name": "fallback_table",
                        }
                    }
                ),
                encoding="utf-8",
            )

            mapping = MODULE.resolve_mapping(target, [primary, fallback], [])
            resolved = mapping["tables"][table_hash]
            self.assertEqual(resolved["name"], "primary_table")
            self.assertEqual(resolved["columns"][column_hash], "primary_id")

    def test_previous_snapshot_migrates_names_to_new_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_table = "v1_" + "1" * 64
            new_table = "v1_" + "2" * 64
            old_columns = ("3" * 64, "4" * 64)
            new_columns = ("5" * 64, "6" * 64)
            previous = root / "previous.db"
            target = root / "target.db"
            rainbow = root / "rainbow.json"
            previous_mapping = root / "previous_mapping.json"
            make_database(previous, old_table, old_columns)
            make_database(target, new_table, new_columns)
            rainbow.write_text("{}", encoding="utf-8")
            previous_mapping.write_text(
                json.dumps(
                    {
                        "tables": {
                            old_table: {
                                "name": "unit_data",
                                "columns": {
                                    old_columns[0]: "unit_id",
                                    old_columns[1]: "name",
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            mapping = MODULE.resolve_mapping(
                target,
                rainbow,
                [],
                previous_db=previous,
                previous_mapping_path=previous_mapping,
            )
            migrated = mapping["tables"][new_table]
            self.assertEqual(migrated["name"], "unit_data")
            self.assertEqual(migrated["columns"][new_columns[0]], "unit_id")
            self.assertEqual(migrated["columns"][new_columns[1]], "name")


if __name__ == "__main__":
    unittest.main()
