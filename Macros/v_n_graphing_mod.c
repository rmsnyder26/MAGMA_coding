void v_n_graphing_mod (int version = 1) {

  //Reset ROOT
   gROOT->Reset();
   gROOT->SetStyle("Plain");
   gStyle->SetOptTitle(0);
   gStyle->SetOptStat(0);
   gStyle->SetOptDate(111111);   

   TCanvas *c = new TCanvas("c","c",10,10,1500,600);

   c->Divide(2,1);
   // how to grab the TPad and then set attributes (logy, ticks)
   c->cd(1);
   gPad->SetTickx(1);
   gPad->SetTicky(1);
   gPad->SetLogy(1);

   //Load ROOT File of 1M events
   TFile *f0 = new TFile("v_n_fluctuations_MAGMA_mod.root");

   TH1D *hist = (TH1D*) (f0->Get("Energy_Distribution_MAGMA_mod"));

   //Find entrality cuts in order to plot 1% cuts on energy distribution

   double maxrange = 150000.0;
   if (version == 1) maxrange = 30000.0;
 
   double cuts[100+1];
   cuts[0] = 0.0;
   double total = hist->Integral();
   for (int i=1;i<100;i++) {
     for (int j=1;j<=10000;j++) {
       if (hist->Integral(1,j) / total > (0.01 * (double) (100-i))) {
	 cuts[100-i] = hist->GetBinCenter(j);
	 // cout << "percentage = " << i << " cut = " << cuts[i] << endl;
	 break;
       }
     }
   }
   cuts[100] = maxrange;

   TH1D *hist_2 = (TH1D*) hist->Clone();
   hist_2->Rebin(10);
   hist_2->GetYaxis()->SetRangeUser(0.5,1.1*hist_2->GetMaximum());
   hist_2->SetLineColor(kRed);
   hist_2->SetFillColorAlpha(kRed,0.3);
   hist_2->SetXTitle("#bf{Energy Total [arbitrary units]}");
   hist_2->GetXaxis()->SetNdivisions(5);
   hist_2->DrawCopy();

   TLine *tcut1[10];
   TLine *tcut2[10];
   for (int i=0;i<=8;i++) {
     tcut1[i] = new TLine(cuts[10*i],0.5,cuts[10*i],1.1*hist_2->GetMaximum());
     tcut1[i]->Draw("l,same");
   }
   for (int i=90;i<=100;i++) {
     tcut2[i] = new TLine(cuts[i],0.5,cuts[i],1.1*hist_2->GetMaximum());
     gStyle->SetLineStyle(7);
     tcut2[i]->Draw("l,same");
   }

   c->cd(2);
   gPad->SetTickx(1);
   gPad->SetTicky(1);
   
   double kappa2 = 0.28;
   double kappa3 = 0.15;

   TGraph *v22 = (TGraph*) (f0->Get("v2_2_MAGMA_mod"));
   TGraph *v32 = (TGraph*) (f0->Get("v3_2_MAGMA_mod"));
   TGraph *v24 = (TGraph*) (f0->Get("v2_4_MAGMA_mod"));

   TH1D *htemplate = new TH1D("htemplate","htemplate",100,0.0,100.0);
   htemplate->SetXTitle("Centrality");
   htemplate->SetYTitle("v_{n} fluctuations");
   htemplate->GetYaxis()->SetTitleOffset(1.3);
   htemplate->GetYaxis()->SetRangeUser(0.0,0.15);
   htemplate->GetXaxis()->SetRangeUser(0.0,30.0);
   htemplate->GetXaxis()->SetTitleSize(.039);
   htemplate->GetYaxis()->SetTitleSize(.039);
   htemplate->GetXaxis()->SetLabelSize(.039);
   htemplate->GetYaxis()->SetLabelSize(.039);  
   htemplate->DrawCopy();


//    // ATLAS data
//    //================================

   float ATLAS_v2_2_x[30] = {0.497382199, 1.439790576, 2.486910995, 3.429319372, 4.476439791, 5.418848168, 6.465968586, 7.513089005, 8.455497382, 9.502617801, 10.54973822, 11.4921466, 12.53926702, 13.48167539, 14.52879581, 15.47120419, 16.41361257, 17.46073298, 18.5078534, 19.45026178, 20.39267016, 21.54450262, 22.48691099, 23.53403141, 24.47643979, 25.52356021, 26.46596859, 27.51308901, 28.45549738, 29.5026178};

   float ATLAS_v2_2_y[30] = {0.025116279, 0.028837209, 0.033488372, 0.038139535, 0.042790698, 0.04744186, 0.052093023, 0.05627907, 0.06, 0.06372093, 0.067906977, 0.071162791, 0.074883721, 0.077674419, 0.080930233, 0.084186047, 0.086976744, 0.089767442, 0.09255814, 0.095348837, 0.097674419, 0.1, 0.102325581, 0.104651163, 0.106976744, 0.108837209, 0.110697674, 0.11255814, 0.114418605, 0.11627907};
   
   float ATLAS_v2_4_x[28] = {2.48691099476439, 3.42931937172775, 4.47643979057591, 5.52356020942408, 6.46596858638743, 7.40837696335078, 8.45549738219895, 9.50261780104712, 10.4450261780104, 11.4921465968586, 12.4345549738219, 13.4816753926701, 14.4240837696335, 15.4712041884816, 16.413612565445, 17.4607329842931, 18.4031413612565, 19.4502617801047, 20.392670157068, 21.4397905759162, 22.4869109947643, 23.5340314136125, 24.4764397905759, 25.4188481675392, 26.4659685863874, 27.4083769633507, 28.4554973821989, 29.5026178010471};
   
   float ATLAS_v2_4_y[28] = {0.0176744186046511, 0.0246511627906976, 0.0306976744186046, 0.035813953488372, 0.0413953488372093, 0.0455813953488372, 0.0502325581395348, 0.053953488372093, 0.0576744186046511, 0.0613953488372093, 0.0646511627906976, 0.0683720930232558, 0.0716279069767441, 0.0744186046511627, 0.0772093023255814, 0.08, 0.0823255813953488, 0.0851162790697674, 0.087906976744186, 0.0897674418604651, 0.0920930232558139, 0.093953488372093, 0.0958139534883721, 0.0976744186046511, 0.0995348837209302, 0.100930232558139, 0.102325581395348, 0.104186046511627};
   
   float ATLAS_v3_2_x[15] = {1.02094240837696, 3.01047120418848, 5, 6.98952879581151, 8.97905759162303, 10.9685863874345, 12.958115183246, 14.9476439790575, 16.9371727748691, 18.9267015706806, 20.9162303664921, 22.9057591623036, 24.9999999999999, 26.9895287958115, 28.979057591623};
   
   float ATLAS_v3_2_y[15] = {0.0260465116279069, 0.0288372093023255, 0.0306976744186046, 0.0320930232558139, 0.0330232558139535, 0.033953488372093, 0.0348837209302325, 0.035813953488372, 0.0367441860465116, 0.0376744186046511, 0.0386046511627907, 0.0395348837209302, 0.04, 0.0409302325581395, 0.0413953488372093};

   TGraph *atlasv22 = new TGraph(30,ATLAS_v2_2_x,ATLAS_v2_2_y);
   TGraph *atlasv24 = new TGraph(28,ATLAS_v2_4_x,ATLAS_v2_4_y);
   TGraph *atlasv32 = new TGraph(15,ATLAS_v3_2_x,ATLAS_v3_2_y);

   atlasv22->SetMarkerStyle(24);
   atlasv22->Draw("p,same");
   atlasv24->SetMarkerStyle(25);
   atlasv24->Draw("p,same");
   atlasv32->SetMarkerStyle(28);
   atlasv32->Draw("p,same");

   v22->SetMarkerStyle(20);
   v24->SetMarkerStyle(21);
   v32->SetMarkerStyle(28);
   v22->SetLineWidth(2);
   v24->SetLineWidth(2);
   v32->SetLineWidth(2);
   v22->SetLineColor(kRed);
   v24->SetLineColor(kAzure);
   v32->SetLineColor(kGreen+2);
   v22->Draw("l,same");
   v24->SetMarkerColor(kBlue);
   v24->Draw("l,same");
   v32->SetMarkerColor(kRed);
   v32->Draw("l,same");

   char footext[100];
   if (version == 0) sprintf(footext,"MAGMA PbPb [A #times B_{WS}+A_{WS} #times B]",total/1.e6);
   if (version == 1) sprintf(footext,"MAGMA PbPb [A #times B]",total/1.e6);
   TLegend *tleg = new TLegend(0.125,0.65,0.575,0.9,footext,"brNDC");
   tleg->SetLineStyle(1);
   sprintf(footext,"v_{2} {2}; #Kappa_{2} = %3.2f",kappa2);
   tleg->AddEntry(v22,footext,"l");
   sprintf(footext,"v_{2} {4}; #Kappa_{2} = %3.2f",kappa2);
   tleg->AddEntry(v24,footext,"l");
   sprintf(footext,"v_{3} {2}; #Kappa_{3} = %3.2f",kappa3);   
   tleg->AddEntry(v32,footext,"l");   
   tleg->AddEntry(atlasv22,"ATLAS data","p");
   tleg->SetTextSize(.031);
   tleg->SetLineStyle(1);
   tleg->Draw("same");   
   
   c->SetRightMargin(c->GetRightMargin()/2);
   c -> SaveAs("v_n_fluctuations_MAGMA_mod.pdf");
} 
   // end of program
