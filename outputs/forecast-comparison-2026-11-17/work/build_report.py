"""Build the requested Word report from verified, dated experiment outputs."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderSVG
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent
OUT = WORK.parent
RESULTS = ROOT/'NLP_Service/evaluation/results/forecast-comparison-2026-11-17'
comparison = json.loads((RESULTS/'comparison.json').read_text())
initial = comparison['blocks']['original_test']
forward = comparison['blocks']['forward_test']
review = json.loads((RESULTS/'itel-fx/backtest.json').read_text())
buffer = json.loads((RESULTS/'buffer-baseline.json').read_text())
classification = json.loads((ROOT/'Scraper/data/collections/repro-2026-11-13/validation-report.json').read_text())
NAME = comparison['models']
METHODS = list(NAME)
RNAME = {'last_value':'Last observed value','recent_mean':'Recent four week mean','history':'History ridge',
         'history_sentiment':'History and sentiment','history_economy':'History and FX',
         'history_sentiment_economy':'History sentiment and FX','current_forecaster':'Legacy univariate selector'}


def f(value, digits=2):
    return f'{value:,.{digits}f}'


def make_chart(name, labels, values, maximum, step, unit):
    drawing = Drawing(620, 238)
    drawing.add(Rect(0,0,620,238,fillColor=colors.white,strokeColor=None))
    chart = HorizontalBarChart()
    chart.x, chart.y, chart.width, chart.height = 195, 38, 345, 178
    chart.data = [list(reversed(values))]
    chart.categoryAxis.categoryNames = list(reversed(labels))
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 10
    chart.categoryAxis.labels.boxAnchor = 'e'
    chart.categoryAxis.labels.dx = -8
    chart.categoryAxis.strokeColor = colors.HexColor('#A0A8B0')
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, maximum, step
    chart.valueAxis.labels.fontSize = 9
    chart.valueAxis.labelTextFormat = lambda n: f'{n:,.0f}'
    chart.valueAxis.strokeColor = colors.HexColor('#A0A8B0')
    chart.valueAxis.visibleGrid = True
    chart.valueAxis.gridStrokeColor = colors.HexColor('#E5E7EB')
    chart.barSpacing = 8
    chart.bars.strokeColor = None
    for i, label in enumerate(reversed(labels)):
        chart.bars[(0,i)].fillColor = colors.HexColor('#6B63A4' if 'sentiment' in label.lower() else '#527C9C')
    chart.barLabelFormat = lambda n: f'{n:,.2f}'
    chart.barLabels.fontName = 'Helvetica'
    chart.barLabels.fontSize = 9
    chart.barLabels.nudge = 7
    chart.barLabels.boxAnchor = 'w'
    drawing.add(chart)
    drawing.add(String(366, 7, unit+'    Lower error is better',textAnchor='middle',fontName='Helvetica',fontSize=10))
    svg = WORK/(name+'.svg')
    svg.write_text(renderSVG.drawToString(drawing))
    return svg


chart_files = [
    make_chart('olist-original', [NAME[m] for m in METHODS], [initial['summary'][m]['mae'] for m in METHODS],65000,10000,'Mean absolute error in BRL'),
    make_chart('olist-forward', [NAME[m] for m in METHODS], [forward['summary'][m]['mae'] for m in METHODS],75000,15000,'Mean absolute error in BRL'),
    make_chart('buffer', ['Last published MRR','Three report mean','Local drift'],[buffer['test'][m]['mae'] for m in ['last_report','three_report_mean','local_drift']],125000,25000,'Mean absolute error in USD'),
]
node = '/Users/oseimuohanitua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
subprocess.run([node, str(WORK/'rasterize.mjs'), *map(str,chart_files)],check=True)

doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin, section.bottom_margin = Inches(.75), Inches(.7)
section.left_margin, section.right_margin = Inches(.8), Inches(.8)
section.footer_distance = Inches(.3)
styles = doc.styles
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
    styles[name].font.name = 'Arial'
    styles[name].font.color.rgb = RGBColor(0,0,0)
styles['Normal'].font.size = Pt(11)
styles['Normal'].paragraph_format.line_spacing = 1.12
styles['Normal'].paragraph_format.space_after = Pt(7)
styles['Title'].font.size = Pt(24)
styles['Title'].paragraph_format.space_after = Pt(12)
styles['Subtitle'].font.size = Pt(12)
styles['Subtitle'].font.italic = False
styles['Subtitle'].paragraph_format.space_after = Pt(8)
styles['Heading 1'].font.size = Pt(16)
styles['Heading 1'].paragraph_format.space_before = Pt(0)
styles['Heading 1'].paragraph_format.space_after = Pt(12)
styles['Heading 2'].font.size = Pt(12)
styles['Heading 2'].paragraph_format.space_before = Pt(10)
styles['Heading 2'].paragraph_format.space_after = Pt(6)
styles['Caption'].font.size = Pt(9.5)
styles['Caption'].font.italic = False
styles['Caption'].paragraph_format.space_after = Pt(8)
doc.core_properties.title = 'Comparison of Forecasting Approaches'
doc.core_properties.subject = 'Measured comparisons of financial history sentiment review volume and exchange rates'
doc.core_properties.author = 'Pulseboard project'
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = footer.add_run('Page ')
run.font.size = Pt(9)
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); footer._p.append(field)


def p(text, bold=False):
    para = doc.add_paragraph()
    para.add_run(text).bold = bold
    return para


def h(text):
    doc.add_heading(text,level=1)


def sub(text):
    doc.add_heading(text,level=2)


def page(title):
    doc.add_page_break();h(title)


def table(headers, rows, widths, digits=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    total_width = t._tbl.tblPr.find(qn('w:tblW'))
    total_width.set(qn('w:type'),'dxa')
    total_width.set(qn('w:w'),str(round(sum(widths)*1440)))
    for col, width in zip(t.columns,widths): col.width = Inches(width)
    for c, text, width in zip(t.rows[0].cells, headers,widths):
        c.width=Inches(width);c.text=text
    header = t.rows[0]._tr.get_or_add_trPr()
    repeat=OxmlElement('w:tblHeader');header.append(repeat)
    for row in rows:
        cells=t.add_row().cells
        for i,(cell,text,width) in enumerate(zip(cells,row,widths)):
            cell.width=Inches(width);cell.text=str(text)
    for ri,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        for ci,cell in enumerate(row.cells):
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr=cell._tc.get_or_add_tcPr()
            shading=OxmlElement('w:shd');shading.set(qn('w:fill'),'263A50' if ri==0 else ('F0F4F7' if ri%2==0 else 'FFFFFF'));tcpr.append(shading)
            margins=OxmlElement('w:tcMar')
            for tag,val in [('top','95'),('bottom','95'),('left','110'),('right','110')]:
                e=OxmlElement('w:'+tag);e.set(qn('w:w'),val);e.set(qn('w:type'),'dxa');margins.append(e)
            tcpr.append(margins)
            borders=OxmlElement('w:tcBorders')
            for tag in ['top','left','bottom','right']:
                e=OxmlElement('w:'+tag);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            tcpr.append(borders)
            for para in cell.paragraphs:
                para.paragraph_format.space_after=Pt(0)
                para.paragraph_format.line_spacing=1.05
                para.paragraph_format.left_indent=Inches(0)
                para.paragraph_format.right_indent=Inches(0)
                para.paragraph_format.first_line_indent=Inches(0)
                numeric = re.fullmatch(r'[-+]?\d[\d,.% ]*',para.text) is not None
                para.alignment = WD_ALIGN_PARAGRAPH.RIGHT if ci>0 and numeric else WD_ALIGN_PARAGRAPH.LEFT
                if para.text in ('Yes','No'): para.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size=Pt(10)
                    run.font.color.rgb=RGBColor(255,255,255) if ri==0 else RGBColor(0,0,0)
                    run.bold=ri==0
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return t


def figure(name, caption):
    paragraph=doc.add_paragraph()
    paragraph.paragraph_format.space_after=Pt(2)
    paragraph.paragraph_format.keep_with_next=True
    run=paragraph.add_run()
    run.add_picture(str(WORK/(name+'.png')),width=Inches(6.85))
    props=run._r.xpath('.//wp:docPr')[0];props.set('descr',caption)
    doc.add_paragraph(caption,style='Caption')


def link(paragraph, text, url):
    rel=paragraph.part.relate_to(url,RT.HYPERLINK,is_external=True)
    node=OxmlElement('w:hyperlink');node.set(qn('r:id'),rel)
    r=OxmlElement('w:r');pr=OxmlElement('w:rPr')
    color=OxmlElement('w:color');color.set(qn('w:val'),'164A70');pr.append(color);r.append(pr)
    size=OxmlElement('w:sz');size.set(qn('w:val'),'19');pr.append(size)
    fonts=OxmlElement('w:rFonts');fonts.set(qn('w:ascii'),'Arial');fonts.set(qn('w:hAnsi'),'Arial');pr.append(fonts)
    tt=OxmlElement('w:t');tt.text=text;r.append(tt);node.append(r);paragraph._p.append(node)


doc.add_paragraph('Comparison of Forecasting Approaches',style='Title')
doc.add_paragraph('Sentiment financial history review activity and exchange rates',style='Subtitle')
p('Pulseboard project evaluation report   17 November 2026')
sub('Main finding')
p('Sentiment does not improve every forecast. Its value depends on the outcome, forecast horizon and comparison baseline. The reproduced experiments show useful improvements for some Nigerian product rating and four-week review forecasts, but they do not establish additional predictive value beyond review counts for Olist order value.')
p('This report compares the implemented approaches using the same eligible dates within each experiment. It includes simple statistical baselines, regression using financial history, regression with review counts, regression with sentiment, and variants using a lagged Nigerian exchange-rate feature. Results from different targets are reported separately.')
sub('Results that matter for the project')
p('For Olist order value, the four-week moving mean had the lowest error across the 17-week original test: BRL '+f(initial['summary']['four_week_mean']['mae'])+' MAE. The sentiment model recorded BRL '+f(initial['summary']['sentiment']['mae'])+'. Sentiment improved on history-only ridge, but not on the review-count control or the moving mean.')
p('Across four later Olist weeks, carrying forward the last week performed best among the six tested approaches. These four observations are too few to establish a generally superior method.')
p('For the itel product, sentiment reduced four-week-ahead review-count MAE by 15.29% relative to history-only ridge. It also reduced rating MAE by 8.24% at one week and 7.35% at four weeks. Adding FX did not improve every outcome.')
p('Sentiment remains an explicit input to the project model. Keeping it satisfies the project scope; it must not be presented as proof that sentiment is always the most accurate forecasting avenue.')
sub('Scope of this test run')
p('The experiments were rerun on 17 November 2026 using preserved data cutoffs and fixed model settings. The original test periods had already been examined. This rerun verifies reproducibility and adds explicit simple-baseline comparisons; it is not a newly independent test, a new training-data collection or a production accuracy guarantee.')

page('Forecasting approaches and predictors')
p('The main commercial comparison forecasts the monetary value of approved order items in the next Monday-to-Sunday week. Each method sees only information from earlier closed weeks. Adding a predictor creates a different model avenue, not a different definition of the target.')
table(['Approach','Information used','Sentiment'],[
    ['Last week','Most recent closed weekly order value','No'],
    ['Four week mean','Average of the last four closed weekly values','No'],
    ['Local drift','Last value plus recent change across three intervals','No'],
    ['Financial history ridge','Lagged values and approved order counts','No'],
    ['History and review counts','Financial predictors plus lagged text-review volume','No'],
    ['History counts and sentiment','The same predictors plus lagged polarity scores','Yes'],
],[2.0,4.05,.85])
sub('How the regression avenues differ')
p('Financial ridge uses five predictors: log-transformed last-week value, value two weeks earlier, the recent four-week mean value, last-week order count and the recent four-week mean order count. The review-volume control adds two predictors: last-week and recent-average text-review counts.')
p('The sentiment model adds last-week mean compound score, the four-week mean score weighted by scored-review counts, last-week negative-review share and two missingness indicators. It therefore has 12 predictors. An absent score remains missing in the prepared data; regression uses training-only median imputation plus indicators.')
p('Ridge regression penalizes large coefficients to stabilize fitting with correlated predictors and short histories. All commercial ridge models predict log of one plus order value, then transform the forecast back to BRL. Predictors are standardized within each training fit. No lognormal mean-bias correction is applied.')
sub('What the economic avenue means here')
p('A separate Nigerian review experiment adds a lagged percentage change in the CBN NFEM NGN-per-USD rate. Its variants are history, history with sentiment, history with FX, and history with both sentiment and FX. The economic input is one exchange-rate feature, not a complete model of inflation, GDP or a business sector. [3]')
p('Nigerian FX data from 2024 to 2026 is not combined with Brazilian transactions from 2017 to 2018. Doing so would mismatch both geography and dates. Sentiment-only monetary prediction is also not tested: the implemented model uses text scores alongside the business scale supplied by order history.')

page('Data and evaluation design')
table(['Dataset','Role and target','Coverage used'],[
    ['Olist original window','Approved item value excluding freight in BRL','82 weeks and 37,698 texts'],
    ['Olist extended window','Same store and target with four later weeks','86 weeks and 41,110 texts'],
    ['Jumia itel product','Weekly review count and mean customer stars','201 reviews and 36 closed weeks'],
    ['Buffer reports','Monthly recurring revenue in USD','32 reported monthly periods'],
    ['RePro benchmark','Human reference sentiment labels','7,975 eligible three-class texts'],
],[1.6,3.5,1.8])
p('Olist v2 supplies linked orders, item prices and review answer timestamps. The target sums item prices by approval week and excludes freight. Final delivered or cancelled status is not used to retrospectively filter approved orders. Refunds, fees, costs and profit are not reconstructed. This is a store portfolio across sellers, not a separate firm for every item. [1]')
sub('Commercial forecast protocol')
p('Four weeks provide lagged predictors, leaving 78 feature/target pairs in the original window. There are 48 initial training pairs, 13 validation targets from 1 January to 26 March 2018, and 17 original test targets from 2 April to 23 July. The later targets are 30 July, 6 August, 13 August and 20 August 2018.')
p('The earlier validation selected ridge penalties of 0.1 for financial history, 1.0 for review volume and 0.1 for sentiment from the declared grid 0.1, 1, 10 and 100. Those settings stay fixed. Comparisons therefore evaluate validation-selected model families, not the isolated causal effect of one feature while every other setting is held constant.')
p('At each origin, models refit on earlier labelled pairs. An earlier test outcome can enter a later fit after that week closes. This is expanding one-week-ahead evaluation, not one forecast issued 17 weeks in advance. Review features use customer answer time rather than the corresponding order date. Missing sales weeks are not invented as zero.')
sub('Nigerian review protocol')
p('The original collection cutoff remains 29 October 2026. The unfinished week is excluded, leaving 193 reviews in 36 completed calendar weeks. The last eight targets run from 31 August to 19 October 2026. A four-week horizon predicts the individual weekly outcome four weeks ahead, not the total of four weeks.')
p('All review variants use matched eligible folds, four-week feature windows, at least 12 earlier training examples and fixed ridge penalty 10. FX observations receive a seven-day assumed availability lag. Historical release timestamps and real-time data vintages are unavailable. Repeating the experiment on 17 November does not extend its data cutoff.')

page('Order value results on the original test')
p('All six methods predict the same 17 weekly outcomes from 2 April to 23 July 2018. Values below are errors in BRL except WAPE. Lower error is better. The regression settings were selected on the earlier validation window, not this test.')
table(['Method','MAE in BRL','RMSE in BRL','WAPE'],[[NAME[m],f(initial['summary'][m]['mae']),f(initial['summary'][m]['rmse']),f(initial['summary'][m]['wape_percent'])+'%'] for m in METHODS],[2.8,1.35,1.4,1.35])
figure('olist-original','Figure 1  Original test mean absolute error across 17 matched weeks')
p('The moving mean has the lowest observed MAE and RMSE. Financial-history ridge was the financial family chosen by validation, yet it does not beat the moving mean on this later block. That change in ranking is evidence that selecting a model is different from knowing its future performance.')
p('Relative to financial-history ridge, adding review counts reduces MAE by 9.32%, while the sentiment family reduces it by 7.72%. Against the stronger review-count control, sentiment increases MAE by 1.76%. Against the moving mean, sentiment increases MAE by 3.54%. A comparison only against history ridge would overstate the evidence for text sentiment.')
p('The sentiment model has mean prediction error of minus BRL '+f(abs(initial['summary']['sentiment']['mean_error']))+', indicating underprediction on average in this block. Neither the small differences between the leading models nor 17 dependent weekly outcomes justify a statistical significance or universal superiority claim.')

page('Forward order value results and uncertainty')
p('The four additional target weeks were first evaluated under the frozen forward protocol on 13 November. Their results are reproduced here. They extend the same Olist store history and do not add an independent company. No model was retuned after inspecting these outcomes.')
table(['Method','MAE in BRL','RMSE in BRL','WAPE'],[[NAME[m],f(forward['summary'][m]['mae']),f(forward['summary'][m]['rmse']),f(forward['summary'][m]['wape_percent'])+'%'] for m in METHODS],[2.8,1.35,1.4,1.35])
figure('olist-forward','Figure 2  Forward test mean absolute error across four matched weeks')
p('Last week is the best observed baseline on this short extension. The moving mean, which led the original test, performs worst here. Four weeks cannot reveal whether this reversal reflects persistent change or ordinary short-sample variability.')
p('Sentiment MAE is 3.38% worse than financial-history ridge and 1.96% worse than the review-count control on the forward block. These results do not establish incremental financial forecasting value from the chosen sentiment features.')
p('Nominal 90% ranges use the last 20 earlier absolute log errors, with at least 12 calibration errors required. The sentiment ranges cover 4 of 4 outcomes, but their mean width is BRL '+f(forward['summary']['sentiment']['mean_interval_width'])+'. Wide ranges can achieve coverage while providing limited precision. Temporal dependence prevents a distribution-free coverage guarantee; 4 of 4 is not 100% future forecast accuracy.')

def evaluation(target):
    return next(r for r in review['evaluations'] if r['target']==target)


def review_rows(target):
    lookup={(r['model'],r['horizon_weeks']):r for r in evaluation(target)['summary']}
    methods=[m for m in RNAME if (m,1) in lookup]
    return [[RNAME[m],f(lookup[m,1]['mae'],4),f(lookup[m,1]['rmse'],4),f(lookup[m,4]['mae'],4),f(lookup[m,4]['rmse'],4)] for m in methods]


page('Review activity with sentiment and exchange rates')
p('This experiment forecasts the number of text reviews for the Jumia itel product. It does not forecast units sold, sales revenue or profit. Each model is evaluated on eight matched target weeks at each horizon; counts are bounded below by zero.')
table(['Model','1 week MAE','1 week RMSE','4 week MAE','4 week RMSE'],review_rows('review_count'),[2.55,1.08,1.09,1.08,1.1])
p('The last-observed-value baseline and the legacy univariate selector tie at the one-week horizon. The selector uses the older review-series forecasting code; it is not the new commercial sentiment model and its equality to the naive result is not an independent confirmation.')
sub('Incremental value of sentiment')
p('At one week, history with sentiment has MAE 3.1167 versus 3.0884 for history alone, a 0.92% deterioration. At four weeks, sentiment improves MAE from 4.4349 to 3.7567, a 15.29% reduction. The same predictor can help at one horizon and fail at another.')
p('The combined sentiment-and-FX model improves four-week MAE by 14.97% over history with FX, but it is 1.14% worse than sentiment without FX. Adding more inputs is therefore not automatically better.')
sub('Incremental value of the economic input')
p('FX alone makes history-ridge MAE 3.30% worse at one week and 0.75% worse at four weeks. A possible economic mechanism for changing review activity is not evidence that this particular exchange-rate feature improves prediction.')
p('The regressions use identical eligible training rows and fixed penalty 10. This supports a cleaner feature comparison within this small case than the separately validation-tuned commercial families. Nevertheless, eight test weeks and one product provide limited evidence. Reviews may reflect delivery, product quality and customer selection rather than demand alone.')
p('The retained CBN file contains 471 rate observations from 2 December 2024 through 28 October 2026. Only eligible earlier windows enter a fold. The seven-day availability lag is a conservative modelling assumption, not a verified record of publication time. [3]')

page('Customer ratings with sentiment and exchange rates')
p('The second Nigerian target is the average of actual customer star ratings within a week. Stars are kept separate from text sentiment. Errors are measured in star points, and predicted ratings are bounded to the valid one-to-five scale. Every row below uses eight target weeks at each horizon.')
table(['Model','1 week MAE','1 week RMSE','4 week MAE','4 week RMSE'],review_rows('average_rating'),[2.55,1.08,1.09,1.08,1.1])
sub('What changes when sentiment is added')
p('History with sentiment is the best observed one-week rating model, with MAE 0.3200 stars. It improves on history alone by 8.24%. The combined sentiment-and-FX model has slightly higher one-week MAE, 0.3234 stars.')
p('At four weeks, history with sentiment improves on history alone by 7.35%. The combined model has the lowest observed MAE, 0.2843 stars. Adding FX after sentiment reduces MAE by a further 1.38% in this block. That small reduction is descriptive, not proof of a general economic effect.')
table(['Comparison','1 week MAE change','4 week MAE change'],[
    ['Add sentiment to history','8.24% lower','7.35% lower'],
    ['Add FX to history','1.02% higher','0.18% higher'],
    ['Add FX after sentiment','1.07% higher','1.38% lower'],
],[3.1,1.9,1.9])
p('Sentiment plausibly helps rating prediction because both summarize customer experience. This relationship is different from predicting a monetary outcome. Good rating forecasts cannot be presented as evidence that revenue or profit has been predicted accurately.')
p('The review sample is strongly skewed towards high ratings: 159 of the 201 source reviews have five stars. Its rating average can differ from the product page aggregate because the collected dataset contains text reviews rather than every star-only rating. This imbalance limits conclusions about negative-customer experience.')
p('No Jumia text-level human sentiment reference set was created in this experiment. The independent RePro classification check concerns Portuguese reviews and does not certify classification accuracy for this English or Pidgin application case.')

page('Monthly recurring revenue as a financial baseline')
p('Buffer provides a separate financial-history experiment. It asks whether simple published-history methods can forecast monthly recurring revenue in USD. MRR is a subscription run rate, not accounting sales, cash receipts or profit. It is not pooled with Olist order value or Jumia review metrics. [4]')
p('The collection has 32 individually identified monthly reports from January 2023 to December 2025. Targets July to December 2024 select the method, while January to July 2025 provide seven test months. A forecast made on the first day of a target month can use only reports published on strictly earlier dates.')
table(['Method','Validation MAE USD','Test MAE USD','Test WAPE'],[[label,f(buffer['validation'][m]['mae']),f(buffer['test'][m]['mae']),f(buffer['test'][m]['wape_percent'])+'%'] for m,label in [('last_report','Last published MRR'),('three_report_mean','Three report mean'),('local_drift','Calendar aware local drift')]],[2.25,1.65,1.6,1.4])
figure('buffer','Figure 3  Buffer MRR forecast error across seven monthly test targets')
p('Local drift has the lowest validation error and the lowest observed test error in this case. Its test MAE is USD '+f(buffer['test']['local_drift']['mae'])+'. The calculation accounts for elapsed calendar months and report delays; it does not pretend that the latest available report always describes the immediately preceding month.')
p('Buffer changed cancellation recognition in its MRR calculation in August 2025. Later values are excluded from the comparable-regime test rather than interpreted as a pure commercial decline. Older reports are not artificially restated. [4]')
p('The available Buffer app feedback yields only two aligned monthly examples, so no Buffer sentiment-enhanced financial model is fitted. A strong financial-only result is useful as a baseline, but it does not measure sentiment contribution. Seven monthly test targets and unverified historical document revisions remain limitations.')

page('Sentiment classification and forecast reliability')
p('Words are first processed by the sentiment classifier. The forecasting regression receives numeric summaries, not raw words. The compound score is the winning label confidence with a positive or negative sign, and zero for neutral. It is not VADER and it is not a calibrated probability that the business will succeed.')
p('The multilingual model is CardiffNLP XLM-R at its pinned revision. Its sentiment fine-tuning includes Portuguese; the Olist and RePro runs use the general route without translation or Pidgin routing. The sentiment network is not retrained when the forecasting regression coefficients are fitted. [5]')
sub('Human reference benchmark')
p('The author-hosted RePro CSV contains 10,003 rows. Preparation excludes 2,018 mixed-polarity records, five exact cleaned-text Olist overlaps and five duplicate texts. Mixed polarity is not relabelled neutral. The retained 7,975 references come from human polarity annotations, not from customer stars. [2]')
table(['Class','Support','Precision','Recall','F1'],[[label.title(),str(classification['per_class'][label]['support']),f(classification['per_class'][label]['precision']*100)+'%',f(classification['per_class'][label]['recall']*100)+'%',f(classification['per_class'][label]['f1'],3)] for label in ['negative','neutral','positive']],[1.55,.95,1.45,1.45,1.5])
p('Overall accuracy is 91.49%, macro-F1 is 0.803 and balanced accuracy is 89.10%. The majority-class accuracy baseline is 51.75%. These classification measures describe agreement with eligible three-class reference labels, not the accuracy of a financial forecast.')
p('Neutral precision is only 36.75%. The classifier assigns neutral to 445 human-negative and 135 human-positive examples, which can weaken the information retained in a zero compound score. Mixed reviews excluded from this benchmark are another substantive limitation.')
p('The check supports continued Portuguese e-commerce experimentation. It is not an Olist-specific annotation audit or validation of English and Nigerian Pidgin accuracy. Exact-text overlap removal cannot prove absence of related upstream pretraining text. The pretrained model also postdates the 2017 to 2018 transactions; these are retrospective feature experiments.')
p('Olist and RePro are used for academic non-commercial research under the explicit CC BY-NC-SA 4.0 terms. RePro metadata frontmatter differs from its detailed licence text; the stricter explicit licensing terms are retained. The model has not been tuned to this benchmark. [1, 2]')

page('Interpretation and implications for the project')
sub('Why a different model wins in different places')
p('Persistence can work when recent levels are informative. A moving mean can reduce short-term noise but respond slowly to change. Drift can extrapolate growth, yet overshoot if the trend reverses. Regression can combine predictors but can also learn unstable relationships from short or noisy histories. The observed ranking changes are consistent with these tradeoffs; the tests do not prove which mechanism caused them.')
p('The additional review-count control is essential. More reviews may carry information about activity regardless of whether their language is positive or negative. In the Olist original test, some improvement relative to history alone can be obtained without using polarity. Attributing all of that improvement to sentiment would be misleading.')
sub('What the error measures mean')
p('MAE is the average absolute difference between forecast and observed outcome. RMSE gives larger errors greater influence by squaring errors before averaging and taking the square root. Both retain the outcome unit: BRL, USD, reviews or star points. WAPE divides total absolute error by total absolute actual value and expresses the ratio as a percentage. [6]')
p('An error reduction is relative to a named baseline on the same dates. It is not a percentage increase in business performance. Subtracting WAPE from 100 does not produce a calibrated forecast success probability. Currency errors from Brazil cannot be compared numerically with Nigerian review-count errors or converted to Nigerian business accuracy without evidence.')
sub('What should remain in the application')
p('The displayed commercial model retains lagged sentiment as required by the project scope. Its dashboard should continue to show actual order values, the next-week estimate, an estimated range, historical errors, source cutoff and controls. The current implementation does this and refuses forecasts when matching sales or sentiment history is missing.')
p('Keeping sentiment is defensible as a research design choice. The defensible empirical claim is that sentiment was incorporated and evaluated, with mixed results. It is not defensible to claim that sentiment always outperformed alternatives, caused sales growth, or established profit predictions.')
sub('Next evidence needed')
p('Reserve genuinely unexamined businesses or later periods for the next comparison. Review classification errors and response delays using development folds, then freeze any change before a new test. More company histories, independent in-domain labels, verified data availability and actual costs or refunds would support stronger scope-specific claims. The already inspected test blocks must not be relabelled fresh holdouts.')

page('Reproduction verification and references')
p('The rerun reproduced the original Olist regression errors to numerical tolerance below 0.0000001 BRL in MAE. The comparison script verifies source hashes, matches scored texts to their prepared records and requires identical dates for all six commercial methods. It writes per-week predictions and error summaries without changing application forecasts or source snapshots.')
p('Software checks completed on 17 November 2026: 138 Python service and scraper tests passed, with two optional browser tests skipped; 73 Laravel tests passed with 516 assertions. These tests check implementation behavior, not statistical generalization. No parameters were optimized on the reported test blocks during this rerun.')
sub('Reproduction entry points')
p('Run from the project root with the existing Python environment and preserved source/model files. New results are stored under NLP_Service/evaluation/results/forecast-comparison-2026-11-17. The Jumia script preserves its 29 October collection cutoff. Existing outputs should be kept when choosing a new run directory.')
for line in [
    'NLP_Service/scripts/compare_forecast_avenues.py  --snapshot <Olist forward snapshot>  --output <comparison.json>',
    'NLP_Service/scripts/evaluate_olist.py  --snapshot <Olist original snapshot>  --output <olist-original.json>',
    'NLP_Service/scripts/backtest_business.py  --reviews <itel reviews.raw.json>  --as-of 2026-10-29  --output <new directory>',
    'NLP_Service/scripts/evaluate_commercial_baseline.py  --financials <buffer-financials.json>  --output <buffer-baseline.json>',
]:
    para=p(line);para.paragraph_format.line_spacing=1.05;para.paragraph_format.space_after=Pt(5)
    for run in para.runs:run.font.name='Arial';run.font.size=Pt(9)
p('Each entry point is invoked as .venv/bin/python followed by the script and arguments. The commercial comparison uses fixed penalties 0.1, 1 and 0.1; the Jumia comparison uses penalty 10, one- and four-week horizons, and eight target weeks. Cached sentiment outputs retain pinned model and preprocessing identities.')
sub('Sources and project evidence')
refs=[
    ('[1] Olist. Brazilian E-Commerce Public Dataset, version 2. Original orders, items and reviews.','https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce'),
    ('[2] dos Santos Silva and colleagues. RePro, PROPOR 2024, pages 432 to 440. Human annotation methodology.','https://aclanthology.org/2024.propor-1.44/'),
    ('[3] Central Bank of Nigeria. Nigerian Foreign Exchange Market rates. Preserved observations downloaded 29 October 2026.','https://www.cbn.gov.ng/rates/exchratebycurrency.html'),
    ('[4] Buffer. August 2025 shareholder update, published 19 September 2025. MRR definition change.','https://buffer.com/shareholders/august-2025'),
    ('[5] CardiffNLP. Multilingual XLM-R sentiment model card and documented language coverage.','https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment'),
    ('[6] Hyndman and Athanasopoulos. Forecasting Principles and Practice, third edition, chapter 5. Baselines and evaluation.','https://otexts.com/fpp3/toolbox.html'),
]
for text,url in refs:
    para=doc.add_paragraph();para.paragraph_format.space_after=Pt(5)
    run=para.add_run(text+' ');run.font.size=Pt(9.5)
    link(para,'Source',url)
p('Project evidence: comparison.json; olist-original.json; buffer-baseline.json; itel-fx/backtest.json; the preserved RePro validation-report.json; and the fixed COMMERCIAL_PROTOCOL.md and COMMERCIAL_FORWARD_PROTOCOL.md files. Source URLs were checked on 17 November 2026. All quantitative result tables and figures are calculated from local experiment outputs.')

path = OUT/'Forecasting_Approach_Comparison_Report.docx'
# The default Word template contains a blue Title paragraph border. Remove
# paragraph-border residue rather than carrying it into the report.
for border in list(doc.styles.element.xpath('.//w:pBdr')):
    border.getparent().remove(border)
for border in list(doc.element.xpath('.//w:pBdr')):
    border.getparent().remove(border)
doc.save(path)
manifest={'document':path.name,'created_for_date':'2026-11-17','input_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [RESULTS/'comparison.json',RESULTS/'olist-original.json',RESULTS/'buffer-baseline.json',RESULTS/'itel-fx/backtest.json']},'planned_pages':11}
(WORK/'report-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(path)
