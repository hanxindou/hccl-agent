/** @file test_fattree.c — Unit tests for fattree_allreduce CPU simulation. */
#include "hccl_algorithms.h"
#include <stdio.h>
#include <math.h>

static int trun=0,tpass=0,tfail=0;
#define T(n)  do{trun++;printf("  %-52s ",n);}while(0)
#define OK()  do{printf("PASS\n");tpass++;}while(0)
#define NO(m) do{printf("FAIL — %s\n",m);tfail++;}while(0)
#define EPS  0.0001f

static float go(hcclComm_t c,int32_t r,float v,float*o){
    hcclSetRank(c,r);float recv=-999;
    fattree_allreduce(&v,&recv,1,HCCL_FP32,HCCL_SUM,c);
    if(o)*o=recv;return recv;}

static void t4(void){T("4 ranks [1,2,3,4] → 10");
    int32_t ids[]={0,1,2,3};hcclComm_t c=NULL;hcclCommInit(&c,4,ids);
    float in[]={1,2,3,4},out[4];
    for(int i=0;i<4;i++)go(c,i,in[i],NULL);
    for(int i=0;i<4;i++)out[i]=go(c,i,in[i],NULL);
    int ok=1;for(int i=0;i<4;i++)if(fabsf(out[i]-10)>EPS)ok=0;
    if(ok)OK();else NO("expected 10");hcclCommDestroy(c);}

static void t8(void){T("8 ranks [1..8] → 36");
    int32_t ids[8];for(int i=0;i<8;i++)ids[i]=i;
    hcclComm_t c=NULL;hcclCommInit(&c,8,ids);
    float in[8],out[8];
    for(int i=0;i<8;i++)in[i]=(float)(i+1);
    for(int i=0;i<8;i++)go(c,i,in[i],NULL);
    for(int i=0;i<8;i++)out[i]=go(c,i,in[i],NULL);
    int ok=1;for(int i=0;i<8;i++)if(fabsf(out[i]-36)>EPS)ok=0;
    if(ok)OK();else NO("expected 36");hcclCommDestroy(c);}

static void t16(void){T("16 ranks [1..16] → 136");
    int32_t ids[16];for(int i=0;i<16;i++)ids[i]=i;
    hcclComm_t c=NULL;hcclCommInit(&c,16,ids);
    float in[16],out[16];
    for(int i=0;i<16;i++)in[i]=(float)(i+1);
    for(int i=0;i<16;i++)go(c,i,in[i],NULL);
    for(int i=0;i<16;i++)out[i]=go(c,i,in[i],NULL);
    int ok=1;for(int i=0;i<16;i++)if(fabsf(out[i]-136)>EPS)ok=0;
    if(ok)OK();else NO("expected 136");hcclCommDestroy(c);}

static void tns(void){T("NULL send_buf → INVALID_ARG");
    int32_t ids[]={0};hcclComm_t c=NULL;hcclCommInit(&c,1,ids);hcclSetRank(c,0);
    float r;int rc=fattree_allreduce(NULL,&r,1,HCCL_FP32,HCCL_SUM,c);
    if(rc==HCCL_ERR_INVALID_ARG)OK();else NO("expected INVALID_ARG");hcclCommDestroy(c);}

static void tnr(void){T("NULL recv_buf → INVALID_ARG");
    int32_t ids[]={0};hcclComm_t c=NULL;hcclCommInit(&c,1,ids);hcclSetRank(c,0);
    float s=1;int rc=fattree_allreduce(&s,NULL,1,HCCL_FP32,HCCL_SUM,c);
    if(rc==HCCL_ERR_INVALID_ARG)OK();else NO("expected INVALID_ARG");hcclCommDestroy(c);}

static void tf16(void){T("FP16 → NOT_SUPPORTED");
    int32_t ids[]={0};hcclComm_t c=NULL;hcclCommInit(&c,1,ids);hcclSetRank(c,0);
    float s=1,r;int rc=fattree_allreduce(&s,&r,1,HCCL_FP16,HCCL_SUM,c);
    if(rc==HCCL_ERR_NOT_SUPPORTED)OK();else NO("expected NOT_SUPPORTED");hcclCommDestroy(c);}

static void tp(void){T("PROD → NOT_SUPPORTED");
    int32_t ids[]={0};hcclComm_t c=NULL;hcclCommInit(&c,1,ids);hcclSetRank(c,0);
    float s=1,r;int rc=fattree_allreduce(&s,&r,1,HCCL_FP32,HCCL_PROD,c);
    if(rc==HCCL_ERR_NOT_SUPPORTED)OK();else NO("expected NOT_SUPPORTED");hcclCommDestroy(c);}

int main(void){
    printf("\n============================================\n");
    printf(" test_fattree — Fat-Tree AllReduce\n============================================\n\n");
    t4();t8();t16();tns();tnr();tf16();tp();
    printf("\n============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",trun,tpass,tfail);
    printf("============================================\n\n");
    return tfail>0?1:0;}
