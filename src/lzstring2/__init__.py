from typing import Callable
from string import ascii_uppercase, ascii_lowercase, digits

# Base64 and URI-safe alphabets for encoding
KEY_STR_BASE64 = ascii_uppercase + ascii_lowercase + digits + "+/="
KEY_STR_URI_SAFE = ascii_uppercase + ascii_lowercase + digits + "+-$"

# Cache for reverse lookup dictionaries
_base_reverse_dict: dict[str, dict[str, int]] = {}


def get_base_value(alphabet: str, character: str) -> int:
    """Get the numeric value for a character in the given alphabet."""
    global _base_reverse_dict
    if alphabet not in _base_reverse_dict:
        _base_reverse_dict[alphabet] = {c: i for i, c in enumerate(alphabet)}
    return _base_reverse_dict[alphabet][character]


class LZString:
    @staticmethod
    def _compress(
        uncompressed: str, bits_per_char: int, get_char_from_int: Callable[[int], str]
    ) -> str:
        """Internal compression method."""
        if not uncompressed:
            return ""

        dictionary: dict[str, int] = {}
        dictionary_to_create: dict[str, bool] = {}
        wc = ""
        w = ""
        # Compensate for the first entry which should not count
        enlarge_in = 2
        dict_size = 3
        num_bits = 2
        data: list[str] = []
        data_val = 0
        data_pos = 0

        # Main compression loop

        for c in uncompressed:
            if c not in dictionary:
                dictionary[c] = dict_size
                dict_size += 1
                dictionary_to_create[c] = True
            wc = w + c

            if wc in dictionary:
                w = wc
            else:
                if w in dictionary_to_create:
                    if ord(w[0]) < 256:
                        for _ in range(num_bits):
                            data_val <<= 1

                            if data_pos == bits_per_char - 1:
                                data_pos = 0
                                data.append(get_char_from_int(data_val))
                                data_val = 0
                            else:
                                data_pos += 1

                        value = ord(w[0])

                        for _ in range(8):
                            data_val = (data_val << 1) | (value & 1)
                            if data_pos == bits_per_char - 1:
                                data_pos = 0
                                data.append(get_char_from_int(data_val))
                                data_val = 0
                            else:
                                data_pos += 1
                            value >>= 1
                    else:
                        value = 1

                        for _ in range(num_bits):
                            data_val = (data_val << 1) | value

                            if data_pos == bits_per_char - 1:
                                data_pos = 0
                                data.append(get_char_from_int(data_val))
                                data_val = 0
                            else:
                                data_pos += 1
                            value = 0

                        value = ord(w[0])

                        for _ in range(16):
                            data_val = (data_val << 1) | (value & 1)

                            if data_pos == bits_per_char - 1:
                                data_pos = 0
                                data.append(get_char_from_int(data_val))
                                data_val = 0
                            else:
                                data_pos += 1

                            value >>= 1

                    enlarge_in -= 1

                    if not enlarge_in:
                        enlarge_in = 1 << num_bits
                        num_bits += 1

                    del dictionary_to_create[w]
                else:
                    value = dictionary[w]

                    for i in range(num_bits):
                        data_val = (data_val << 1) | (value & 1)

                        if data_pos == bits_per_char - 1:
                            data_pos = 0
                            data.append(get_char_from_int(data_val))
                            data_val = 0
                        else:
                            data_pos += 1

                        value >>= 1

                enlarge_in -= 1

                if not enlarge_in:
                    enlarge_in = 1 << num_bits
                    num_bits += 1

                # Add wc to the dictionary

                dictionary[wc] = dict_size
                dict_size += 1
                w = c

        # Output the code for w.

        if w:
            if w in dictionary_to_create:
                if ord(w[0]) < 256:
                    for i in range(num_bits):
                        data_val = data_val << 1
                        if data_pos == bits_per_char - 1:
                            data_pos = 0
                            data.append(get_char_from_int(data_val))
                            data_val = 0
                        else:
                            data_pos += 1

                    value = ord(w[0])

                    for i in range(8):
                        data_val = (data_val << 1) | (value & 1)

                        if data_pos == bits_per_char - 1:
                            data_pos = 0
                            data.append(get_char_from_int(data_val))
                            data_val = 0
                        else:
                            data_pos += 1
                        value >>= 1

                else:
                    value = 1
                    for i in range(num_bits):
                        data_val = (data_val << 1) | value
                        if data_pos == bits_per_char - 1:
                            data_pos = 0
                            data.append(get_char_from_int(data_val))
                            data_val = 0
                        else:
                            data_pos += 1
                        value = 0

                    value = ord(w[0])
                    for i in range(16):
                        data_val = (data_val << 1) | (value & 1)
                        if data_pos == bits_per_char - 1:
                            data_pos = 0
                            data.append(get_char_from_int(data_val))
                            data_val = 0
                        else:
                            data_pos += 1
                        value >>= 1

                enlarge_in -= 1

                if not enlarge_in:
                    enlarge_in = 1 << num_bits
                    num_bits += 1

                del dictionary_to_create[w]

            else:
                value = dictionary[w]

                for _ in range(num_bits):
                    data_val = (data_val << 1) | (value & 1)
                    if data_pos == bits_per_char - 1:
                        data_pos = 0
                        data.append(get_char_from_int(data_val))
                        data_val = 0
                    else:
                        data_pos += 1
                    value >>= 1

            enlarge_in -= 1

            if not enlarge_in:
                enlarge_in = 1 << num_bits
                num_bits += 1

        # Mark the end of the stream

        value = 2
        for i in range(num_bits):
            data_val = (data_val << 1) | (value & 1)
            if data_pos == bits_per_char - 1:
                data_pos = 0
                data.append(get_char_from_int(data_val))
                data_val = 0
            else:
                data_pos += 1
            value >>= 1

        # Flush last char

        while True:
            data_val = data_val << 1
            if data_pos == bits_per_char - 1:
                data.append(get_char_from_int(data_val))
                break
            else:
                data_pos += 1

        return "".join(data)

    @staticmethod
    def compress_to_base64(input_str: str) -> str:
        """Compress a string using LZ compression and Base64 encoding."""

        res = LZString._compress(input_str, 6, lambda a: KEY_STR_BASE64[a])

        # Pad the result to create valid Base64
        padding = ["", "===", "==", "="]
        return res + padding[len(res) & 0b11]

    @staticmethod
    def compress_to_encoded_URI_component(input_str: str) -> str:
        """Compress into a string that is already URI encoded."""
        return LZString._compress(input_str, 6, lambda a: KEY_STR_URI_SAFE[a])
