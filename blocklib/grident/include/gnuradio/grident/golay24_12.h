#ifndef INCLUDED_GRIDENT_GOLAY24_12_H
#define INCLUDED_GRIDENT_GOLAY24_12_H

#include <cstdint>

namespace gr {
namespace grident {

struct golay_decode_result {
    uint16_t data = 0;
    int num_errors = -1;
    bool valid = false;
};

class golay24_12
{
public:
    static uint32_t encode(uint16_t data_12);
    static golay_decode_result decode(uint32_t codeword_24);
};

} // namespace grident
} // namespace gr

#endif
