"""Tests for sync sequences, metadata field, and extended profiles."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))

from grident.metadata_field import (
    BANDWIDTH_12_5_KHZ,
    MetadataField,
    callsign_crc_nibble,
    decode_metadata,
    encode_metadata,
    pack_metadata,
    unpack_metadata,
)
from grident.modulation.registry import (
    AX25_1200,
    DMR_4800,
    PROFILE_BY_MODE_ID,
    get_profile_for_mode,
)
from grident.preamble import PreambleField, decode_preamble, encode_preamble, pack_field, unpack_field
from grident.sync_sequences import ALL_SYNC_SEQUENCES, SYNC_BY_NAME, SYNC_NFM


class SyncSequenceTests(unittest.TestCase):
    def test_nfm_bits_match_doc(self) -> None:
        self.assertEqual(SYNC_NFM.as_hex(), "0x5BCA")
        self.assertEqual(len(SYNC_NFM.bits), 16)

    def test_all_sequences_unique_names(self) -> None:
        names = [seq.name for seq in ALL_SYNC_SEQUENCES]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(SYNC_BY_NAME), len(ALL_SYNC_SEQUENCES))


class MetadataFieldTests(unittest.TestCase):
    def test_pack_round_trip(self) -> None:
        field = MetadataField(BANDWIDTH_12_5_KHZ, 7, 0xB)
        raw = pack_metadata(field)
        restored = unpack_metadata(raw)
        self.assertEqual(restored.bandwidth_code, 3)
        self.assertEqual(restored.codec_param, 7)
        self.assertEqual(restored.callsign_nibble, 0xB)

    def test_golay_round_trip(self) -> None:
        field = MetadataField(4, 2, 1)
        codeword = encode_metadata(field)
        decoded, errors, valid = decode_metadata(codeword)
        self.assertTrue(valid)
        assert decoded is not None
        self.assertEqual(decoded.codec_param, 2)
        self.assertEqual(errors, 0)

    def test_callsign_nibble(self) -> None:
        self.assertEqual(callsign_crc_nibble(""), 0)
        self.assertNotEqual(callsign_crc_nibble("LA1B"), 0)


class ExtendedProfileTests(unittest.TestCase):
    def test_assigned_mode_count(self) -> None:
        self.assertGreater(len(PROFILE_BY_MODE_ID), 8)

    def test_dmr_mode(self) -> None:
        profile = get_profile_for_mode(100)
        self.assertEqual(profile.name, DMR_4800.name)

    def test_ax25_mode(self) -> None:
        profile = get_profile_for_mode(150)
        self.assertEqual(profile.name, AX25_1200.name)


class MetadataPreambleAirTests(unittest.TestCase):
    def test_modulate_with_metadata(self) -> None:
        from grident.modulation.registry import NFM_125_4800

        field = PreambleField(mode_id=20, digital=False, metadata_present=True)
        meta = MetadataField(BANDWIDTH_12_5_KHZ, 1, callsign_crc_nibble("TEST"))
        signal, info = NFM_125_4800.modulate_preamble(field, meta)
        self.assertTrue(info["metadata_present"])
        self.assertEqual(info["preamble_bits"], 48)

        decoded = NFM_125_4800.decode_signal(signal)
        assert decoded is not None
        out_field, out_meta, _, valid, _, _, _ = decoded
        assert out_field is not None
        self.assertTrue(valid)
        self.assertTrue(out_field.metadata_present)
        assert out_meta is not None
        self.assertEqual(out_meta.bandwidth_code, BANDWIDTH_12_5_KHZ)


class PreambleBit9Tests(unittest.TestCase):
    def test_metadata_present_flag(self) -> None:
        raw = pack_field(PreambleField(mode_id=20, metadata_present=True))
        field = unpack_field(raw, strict_reserved=False)
        self.assertTrue(field.metadata_present)

    def test_legacy_strict_reserved(self) -> None:
        raw = pack_field(PreambleField(mode_id=20, metadata_present=True))
        with self.assertRaises(ValueError):
            unpack_field(raw, strict_reserved=True)

    def test_primary_only_still_works(self) -> None:
        field = PreambleField(mode_id=110, digital=True)
        codeword = encode_preamble(field)
        decoded, _, valid = decode_preamble(codeword)
        self.assertTrue(valid)
        assert decoded is not None
        self.assertFalse(decoded.metadata_present)


if __name__ == "__main__":
    unittest.main()
