# The struct under test

    typedef enum { MODE_IDLE, MODE_ACTIVE, MODE_FAULT } Mode_t;

    typedef union {
        uint32_t raw;
        struct { uint8_t r, g, b, a; } channel;
    } Pixel_t;

    typedef struct {                   /* depth 3 */
        Mode_t       mode;             /* enum, by name */
        Pixel_t      pixel;            /* union */
        void       (*on_event)(int);   /* function pointer */
        int32_t      samples[4];       /* fixed array */
    } Actuator_t;

    typedef struct {                   /* depth 2 */
        Actuator_t actuators[2];
        char       label[16];
    } Channel_t;

    typedef struct {                   /* depth 1 */
        Channel_t channel;
        uint16_t  id;
    } Device_t;

    typedef struct {                   /* depth 0 (root) */
        Device_t device;
        float     scale;
    } Config_t;

Nesting path exercised: `Config_t` (0) → `.device` `Device_t` (1) →
`.channel` `Channel_t` (2) → `.actuators[i]` `Actuator_t` (3) →
`.pixel` `Pixel_t`, a **union** (4). That is the 4-deep path the pass
criterion names. `Actuator_t` alone also carries the function-pointer
member and the fixed array the criterion requires alongside the union —
all three land at the same tree level so the editor has to handle all of
them without one masking a bug in another.
