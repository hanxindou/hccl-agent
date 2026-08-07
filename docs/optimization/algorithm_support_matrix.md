# Algorithm support matrix

| Algorithm | AllReduce | AllGather | ReduceScatter |
| --- | --- | --- | --- |
| Ring | Supported | Supported | Supported |
| Butterfly | Supported | Supported | Unsupported |
| Mesh | Supported | Unsupported | Supported |
| NHR | Supported | Unsupported | Unsupported |
| Hierarchical | Supported | Unsupported | Unsupported |

Unsupported combinations return `UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR`; fallback is `NONE`. A supported label means an explicit simulator/analytical schedule is produced and invariant-checked, not that an official runtime or real device executed it.
