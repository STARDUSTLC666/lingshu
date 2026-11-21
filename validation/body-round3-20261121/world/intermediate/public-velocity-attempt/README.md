# Intermediate evidence only

This implementation used the twice-rounded public velocity to initialize dynamics. It did not preserve actual endpoint displacement when old coordinates were not quantized to two decimals. Retained for audit; superseded by the raw endpoint displacement implementation. Stay is an explicit stop with zero physical velocity despite the existing coordinate quantization.
