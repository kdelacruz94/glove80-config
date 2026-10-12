/* Host adapters; the pinned hold-tap implementation is inserted without logic edits. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#define DT_HAS_COMPAT_STATUS_OKAY(x) 1
#define IS_ENABLED(x) 0
#define CONFIG_ZMK_BEHAVIOR_HOLD_TAP_MAX_HELD 8
#define CONFIG_ZMK_BEHAVIOR_HOLD_TAP_MAX_CAPTURED_EVENTS 64
#define LOG_MODULE_DECLARE(...)
#define LOG_DBG(...)
#define LOG_ERR(...)
#define DT_INST_FOREACH_STATUS_OKAY(...)
#define ZMK_LISTENER(...)
#define ZMK_SUBSCRIPTION(...)
#define ZMK_BEHAVIOR_OPAQUE 0
#define ZMK_EV_EVENT_BUBBLE 0
#define ZMK_EV_EVENT_CAPTURED 1
#define K_MSEC(x) (x)
#define CONTAINER_OF(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
struct k_work { int unused; };
struct k_work_delayable { struct k_work work; int64_t due; };
static struct k_work_delayable *k_work_delayable_from_work(struct k_work *w) { return CONTAINER_OF(w,struct k_work_delayable,work); }
static int64_t now;
static int64_t k_uptime_get(void) { return now; }
static int k_work_schedule(struct k_work_delayable *w, int delay) { w->due=now+delay; return 0; }
static int k_work_cancel_delayable(struct k_work_delayable *w) { w->due=-1; return 0; }
static void k_work_init_delayable(struct k_work_delayable *w, void (*fn)(struct k_work *)) { w->due=-1; }
static void k_msleep(int delay) { assert(!"unexpected nested replay wait"); }
struct zmk_position_state_changed { int kind; uint32_t position; bool state; int64_t timestamp; };
struct zmk_keycode_state_changed { int kind; uint32_t usage_page, keycode; bool state; int64_t timestamp; };
struct zmk_position_state_changed_event { struct zmk_position_state_changed data; };
struct zmk_keycode_state_changed_event { struct zmk_keycode_state_changed data; };
typedef struct { int kind; } zmk_event_t;
static struct zmk_position_state_changed *as_zmk_position_state_changed(const zmk_event_t *e) { return e->kind==1?(void *)e:NULL; }
static struct zmk_keycode_state_changed *as_zmk_keycode_state_changed(const zmk_event_t *e) { return e->kind==2?(void *)e:NULL; }
static struct zmk_position_state_changed_event copy_raised_zmk_position_state_changed(struct zmk_position_state_changed *e) { return (struct zmk_position_state_changed_event){*e}; }
static struct zmk_keycode_state_changed_event copy_raised_zmk_keycode_state_changed(struct zmk_keycode_state_changed *e) { return (struct zmk_keycode_state_changed_event){*e}; }
static void replay_position(struct zmk_position_state_changed_event e);
static void replay_keycode(struct zmk_keycode_state_changed_event e) { assert(!"unexpected modifier capture"); }
#define ZMK_EVENT_RAISE_AT(e,listener) _Generic((e),struct zmk_position_state_changed_event:replay_position,struct zmk_keycode_state_changed_event:replay_keycode)(e)
struct zmk_listener { int unused; };
struct device { const void *config; };
struct zmk_behavior_binding { char *behavior_dev; uint32_t param1, param2; };
struct zmk_behavior_binding_event { uint32_t position; int64_t timestamp; };
struct behavior_driver_api { int (*binding_pressed)(struct zmk_behavior_binding *,struct zmk_behavior_binding_event); int (*binding_released)(struct zmk_behavior_binding *,struct zmk_behavior_binding_event); };
static const struct device *zmk_behavior_get_binding(char *name);
static int zmk_behavior_invoke_binding(struct zmk_behavior_binding *,struct zmk_behavior_binding_event,bool);
static bool is_mod(uint32_t page,uint32_t key) { return key==1000; }

/* PINNED_HOLD_TAP_SOURCE */

/* KEYMAP_CONFIG */

static struct device devices[2];
static const struct device *zmk_behavior_get_binding(char *name) { return &devices[!strcmp(name,"right")]; }
static const char keys[80] = {[23]='q',[38]='f',[41]='j',[31]='o',[26]='r',[29]='u',[24]='w',[36]='s',[27]='t',[30]='i',[59]='m',[58]='n',[32]='p'};
static char output[256];
static unsigned used, shifts, shift_presses;
static int zmk_behavior_invoke_binding(struct zmk_behavior_binding *b,struct zmk_behavior_binding_event e,bool down) {
    struct zmk_keycode_state_changed kc={2,0,b->param1,down,e.timestamp};
    keycode_state_changed_listener((const zmk_event_t *)&kc);
    if (b->param1==1000) { if (down) { shifts++; shift_presses++; } else { assert(shifts); shifts--; } }
    else if (down) { assert(used+1<sizeof(output)); output[used++]=shifts?b->param1-'a'+'A':b->param1; output[used]=0; }
    return 0;
}
/* Other keys use kp to isolate f/j from the remaining layout behaviors. */
static void replay_position(struct zmk_position_state_changed_event e) {
    struct zmk_behavior_binding_event event={e.data.position,e.data.timestamp};
    struct zmk_behavior_binding b={.behavior_dev=e.data.position==38?"left":"right",.param1=1000,.param2=keys[e.data.position]};
    if (e.data.position==38 || e.data.position==41) {
        if(e.data.state) on_hold_tap_binding_pressed(&b,event); else on_hold_tap_binding_released(&b,event);
    } else { b.param1=keys[e.data.position]; assert(b.param1); zmk_behavior_invoke_binding(&b,event,e.data.state); }
}
static void advance(int64_t time) {
    for (;;) {
        struct active_hold_tap *next=NULL;
        for(unsigned i=0;i<ZMK_BHV_HOLD_TAP_MAX_HELD;i++) {
            struct active_hold_tap *h=&active_hold_taps[i];
            if(h->position!=ZMK_BHV_HOLD_TAP_POSITION_NOT_USED && h->work.due>=0 && h->work.due<=time && (!next || h->work.due<next->work.due)) next=h;
        }
        if(!next) break;
        now=next->work.due; next->work.due=-1;
        behavior_hold_tap_timer_work_handler(&next->work.work);
    }
    now=time;
}
static void key(int pos,bool down,int time) {
    assert(time>=now);
    advance(time);
    struct zmk_position_state_changed_event e={{1,pos,down,time}};
    if(position_state_changed_listener((const zmk_event_t *)&e.data)==ZMK_EV_EVENT_BUBBLE) replay_position(e);
}
static void reset(void) {
    memset(active_hold_taps,0,sizeof(active_hold_taps));
    for(unsigned i=0;i<ZMK_BHV_HOLD_TAP_MAX_HELD;i++) { active_hold_taps[i].position=ZMK_BHV_HOLD_TAP_POSITION_NOT_USED; active_hold_taps[i].work.due=-1; }
    memset(captured_events,0,sizeof(captured_events));
    undecided_hold_tap=NULL; last_tapped=(struct last_tapped){INT32_MIN,INT32_MIN};
    shifts=used=shift_presses=0; output[0]=0; now=0;
}
static unsigned failures, cases;
static void expect(const char *label,const char *wanted,unsigned wanted_shift) {
    cases++;
    if(strcmp(output,wanted) || shifts || shift_presses!=wanted_shift) { failures++; printf("FAIL %s: expected %s, got %s (Shift=%u, presses=%u, wanted=%u)\n",label,wanted,output,shifts,shift_presses,wanted_shift); }
}
static int position(char ch) { for(int i=0;i<80;i++) if(keys[i]==ch) return i; assert(!"unknown letter"); return -1; }
static void word(const char *text,int gap,int dwell,const char *wanted) {
    struct { int pos,time; bool down,used; } events[64];
    int length=strlen(text); assert(length<32);
    for(int i=0;i<length;i++) {
        int pos=position(text[i]),start=1000+i*gap;
        int end=start+dwell+(text[i]=='f'||text[i]=='j'?90:0);
        for(int j=i+1;j<length;j++) if(text[i]==text[j]) { if(end>=1000+j*gap) end=1000+j*gap-1; break; }
        events[2*i]=(typeof(events[0])){pos,start,true,false};
        events[2*i+1]=(typeof(events[0])){pos,end,false,false};
    }
    for(int n=0;n<2*length;n++) {
        int k=-1;
        for(int i=0;i<2*length;i++) if(!events[i].used && (k<0 || events[i].time<events[k].time || (events[i].time==events[k].time && !events[i].down))) k=i;
        key(events[k].pos,events[k].down,events[k].time); events[k].used=true;
    }
    char label[64];
    snprintf(label,sizeof(label),"%s gap=%d dwell=%d",text,gap,dwell);
    expect(label,wanted,strcmp(text,wanted)?1:0);
}
int main(void) {
    devices[0].config=&left_cfg; devices[1].config=&right_cfg;
    reset();
    key(38,true,1000);
        key(31,true,1050);
        key(31,false,1090);
        key(38,false,1130);
        key(26,true,1180);
        key(26,false,1230);
        expect("for nested","for",0);
    reset();
        key(41,true,1000);
        key(29,true,1180);
        key(41,false,1310);
        key(29,false,1340);
        key(36,true,1400);
        key(36,false,1450);
        key(27,true,1500);
        key(27,false,1550);
        expect("same-hand press after timeout","Ust",1);
    for(int side=0;side<2;side++) for(int order=0;order<2;order++) {
        int mod=side?41:38,target=side?24:30; const char *want=side?"jw":"fi";
        reset();
        key(mod,true,1000);
        key(target,true,1050);
        key(order?target:mod,false,1090);
        key(order?mod:target,false,1130);
        expect("cross-hand short tap",want,0);
        reset();
        key(mod,true,1000);
        key(target,true,1120);
        key(order?target:mod,false,1140);
        key(order?mod:target,false,1149);
        expect("released before 150 ms",want,0);
        reset();
        key(mod,true,1000);
        key(side?29:26,true,1100);
        key(mod,false,1700);
        key(side?29:26,false,1750);
        expect("same-hand excludes timeout",side?"ju":"fr",0);
        reset();
        key(mod,true,1000);
        key(target,true,1000+left_cfg.tapping_term_ms+20);
        key(order?target:mod,false,1000+left_cfg.tapping_term_ms+80);
        key(order?mod:target,false,1000+left_cfg.tapping_term_ms+120);
        expect("deliberate Shift",side?"W":"I",1);
    }
    /* Absolute times cover the 150 ms boundary and short deliberate holds. */
    /* A target pressed at 149 ms still capitalizes if f/j overlaps timeout. */
    const int holds[]={149,150,180,250};
    for(int side=0;side<2;side++) for(int order=0;order<2;order++) for(unsigned h=0;h<sizeof(holds)/sizeof(holds[0]);h++) {
        int mod=side?41:38,target=side?23:30,hold=holds[h];
        reset();
        key(mod,true,1000);
        key(target,true,1000+hold);
        key(order?target:mod,false,1000+hold+20);
        key(order?mod:target,false,1000+hold+40);
        expect("Quality/Inventory short hold",side?"Q":"I",1);
    }
    for(int side=0;side<2;side++) {
        int mod=side?41:38;
        reset();
        key(mod,true,1000);
        key(mod,false,1080);
        expect("isolated tap",side?"j":"f",0);
        reset();
        key(31,true,1000);
        key(31,false,1040);
        key(mod,true,1150);
        key(mod,false,2000);
        expect("prior idle forces tap",side?"oj":"of",0);
    }
    const char *words[]={"for","just","if","fun","jump","of","off"};
    /* Fixed 150 ms expectations: rows are gaps 60..180, columns dwells 50..230.
     * f/j dwell adds 90 ms. A word-start timeout loses f/j; subsequent letters
     * capitalize only while Shift remains down. Prior-idle protects if/of/off. */
    const char *expected[7][5][7]={
        {
            {"for","OR","OR","OR","OR","OR","OR"},
            {"for","Or","OR","OR","OR","OR","OR"},
            {"for","Or","Or","Or","OR","OR","OR"},
            {"for","Or","Or","Or","Or","Or","OR"},
            {"for","or","Or","Or","Or","Or","Or"},
        },
        {
            {"just","just","just","just","just","just","just"},
            {"just","just","just","just","just","just","just"},
            {"just","just","just","just","just","just","just"},
            {"just","Ust","Ust","Ust","Ust","Ust","USt"},
            {"just","ust","Ust","Ust","Ust","Ust","Ust"},
        },
        {{NULL}}, /* if stays lowercase */
        {
            {"fun","UN","UN","UN","UN","UN","UN"},
            {"fun","Un","UN","UN","UN","UN","UN"},
            {"fun","Un","Un","Un","UN","UN","UN"},
            {"fun","Un","Un","Un","Un","Un","UN"},
            {"fun","un","Un","Un","Un","Un","Un"},
        },
        {
            {"jump","jump","jump","jump","jump","jump","jump"},
            {"jump","jump","jump","jump","jump","jump","jump"},
            {"jump","jump","jump","jump","jump","jump","jump"},
            {"jump","Ump","Ump","Ump","Ump","Ump","UMp"},
            {"jump","ump","Ump","Ump","Ump","Ump","Ump"},
        },
        {{NULL}}, /* of stays lowercase */
        {{NULL}}, /* off stays lowercase */
    };
    for(unsigned w=0;w<sizeof(words)/sizeof(words[0]);w++) for(int gap=60;gap<=180;gap+=30) for(int dwell=50;dwell<=240;dwell+=30) {
        const char *wanted=expected[w][(gap-60)/30][(dwell-50)/30];
        reset(); word(words[w],gap,dwell,wanted?wanted:words[w]);
    }
    printf("%u/%u traces passed\n",cases-failures,cases);
    return failures?1:0;
}
