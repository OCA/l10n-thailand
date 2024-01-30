# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from decimal import Decimal

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base.models.res_bank import sanitize_account_number


class BankPaymentExport(models.Model):
    _inherit = "bank.payment.export"

    bank = fields.Selection(
        selection_add=[("SICOTHBK", "SCB")],
        ondelete={"SICOTHBK": "cascade"},
    )
    scb_company_id = fields.Char(
        string="SCB Company ID",
        size=12,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_corp_id = fields.Char(
        string="Corp ID",
        size=12,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Corp ID บน Buisness Net",
    )
    scb_for_id = fields.Char(
        string="FOR ID",
        size=20,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Unigue Cust ID บนระบบเงินโอนของ SCB",
    )
    # filter
    scb_is_editable = fields.Boolean(
        compute="_compute_scb_editable",
        string="SCB Editable",
    )
    scb_bank_type = fields.Selection(
        selection=[
            ("1", "1 - Next Day"),
            ("2", "2 - Same Day Afternoon"),
        ],
        default="1",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_outward_remittance = fields.Boolean(
        string="Outward Remittance",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_rate_type = fields.Selection(
        selection=[
            ("FW", "FW - Rate Forward"),
            ("SP", "SP - Rate Spot"),
        ],
        string="Rate Type",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_contract_ref_no = fields.Char(
        string="Forward Contract No. / Deal no.",
        size=20,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_rate = fields.Float(
        string="Rate",
        digits=(3, 7),
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_charge_flag = fields.Selection(
        selection=[
            ("A", "A - Applicant Charge 'OUR'"),
            ("B", "B - Beneficiary Charge 'BEN'"),
        ],
        string="Charge Flag",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_objective_code = fields.Selection(
        selection=[
            ("318004", "318004 - ค่าขนส่งสินค้า"),
            ("318005", "318005 - ค่าเบี้ยประกันภัยและเบี้ยประกันภัยช่วงสำหรับสินค้า"),
            ("318006", "318006 - ค่าสินไหมทดแทนประกันภัยสินค้า"),
            (
                "318007",
                "318007 - ค่าบริการอื่นๆ ที่เกี่ยวกับการขนส่งสินค้าระหว่างประเทศ",
            ),
            ("318009", "318009 - ค่าโดยสาร"),
            (
                "318010",
                "318010 - ค่าบริการต่าง ๆ ที่ให้แก่พาหนะระหว่างประเทศ และค่าขนส่งอื่นๆ",
            ),
            ("318012", "318012 - ค่าใช้จ่ายเดินทาง-นักท่องเที่ยว"),
            ("318013", "318013 - ค่าใช้จ่ายเดินทาง-นักเรียน นักศึกษา"),
            ("318014", "318014 - ค่าใช้จ่ายเดินทางไปต่างประเทศ-อื่นๆ"),
            ("318015", "318015 - ค่าใช้จ่ายบริการด้านสุขภาพ"),
            ("318018", "318018 - ค่าบริการภาครัฐบาล"),
            ("318023", "318023 - ค่าสื่อสารโทรคมนาคม"),
            ("318024", "318024 - ค่ารับเหมาก่อสร้าง"),
            (
                "318025",
                "318025 - ค่ารอยัลตี้ ค่าเครื่องหมายการค้า/สิทธิบัตร และลิขสิทธิ์",
            ),
            (
                "318026",
                "318026 - ค่าเบี้ยประกันภัยและเบี้ยประกันภัยช่วงที่ไม่เกี่ยวกับสินค้า",
            ),
            ("318027", "318027 - ค่าสินไหมทดแทนประกันภัยที่ไม่เกี่ยวกับสินค้า"),
            ("318028", "318028 - ค่าที่ปรึกษา"),
            ("318029", "318029 - ค่าธรรมเนียมและค่านายหน้าทางด้านการเงิน"),
            ("318030", "318030 - ค่าธรรมเนียมและค่านายหน้าอื่นๆ"),
            ("318031", "318031 - ค่าบริการข้อมูลข่าวสาร"),
            ("318032", "318032 - ค่าใช้จ่ายสำนักงานผู้แทน"),
            ("318033", "318033 - ค่าโฆษณา"),
            ("318034", "318034 - ค่าเช่าทรัพย์สิน"),
            ("318035", "318035 - ค่าใช้จ่ายเกี่ยวกับภาพยนตร์ โทรทัศน์ และการแสดงต่างๆ"),
            ("318036", "318036 - ค่าบริการอื่นๆ (โปรดระบุรายละเอียด)"),
            ("318037", "318037 - ค่ารับจ้างผลิตหรือแปรรูป"),
            ("318040", "318040 - รายได้ส่งกลับของแรงงาน"),
            ("318042", "318042 - กำไร"),
            ("318043", "318043 - ปันผล"),
            ("318044", "318044 - ดอกเบี้ยเงินกู้"),
            ("318045", "318045 - ดอกเบี้ยอื่นๆ"),
            (
                "318046",
                "318046 - เงินผลประโยชน์จากการลงทุนและการให้กู้ยืมจากต่างประเทศภาครัฐบาล",
            ),
            ("318052", "318052 - เงินให้เปล่าภาคเอกชน"),
            ("318053", "318053 - เงินให้เปล่าภาครัฐบาล"),
            (
                "318057",
                "318057 - ส่งเงินซึ่งเป็นกรรมสิทธิ์ของคนไทยที่ย้ายถิ่นฐาน"
                "ไปพำนักอยู่ต่างประเทศเป็นการถาวร",
            ),
            (
                "318058",
                "318058 - ส่งเงินมรดกให้แก่ผู้รับมรดก ซึ่งมีถิ่นพำนักถาวรในต่างประเทศ",
            ),
            (
                "318059",
                "318059 - ส่งเงินไปให้ครอบครัวหรือญาติพี่น้อง ซึ่งมีถิ่นพำนักถาวรในต่างประเทศ",
            ),
            (
                "318062",
                "318062 - รับ / ส่งคืน เงินลงทุนธุรกิจในเครือของบุคคลต่างประเทศ "
                "(Foreign Direct Investment)",
            ),
            (
                "318065",
                "318065 - ส่ง / รับคืน เงินลงทุนธุรกิจในเครือของบุคคลไทย "
                "(Thai Direct Investment)",
            ),
            ("318068", "318068 - เงินลงทุนอสังหาริมทรัพย์จากต่างประเทศ (อาคารชุด)"),
            ("318072", "318072 - เงินลงทุนอสังหาริมทรัพย์ในต่างประเทศ"),
            (
                "318076",
                "318076 - เงินลงทุนในหลักทรัพย์จากต่างประเทศ (Foreign Portfolio Investment)",
            ),
            ("318083", "318083 - เงินกู้ยืม (Foreign Loan)"),
            (
                "318086",
                "318086 - เงินกู้ยืมที่เป็นตราสารหนี้ (Foreign Debt Instrument)",
            ),
            ("318090", "318090 - เงินให้กู้ยืม (Thai Loan)"),
            ("318093", "318093 - เงินให้กู้ที่เป็นตราสารหนี้ (Thai Debt Instrument)"),
            ("318097", "318097 - NR ปรับฐานะเงินตราต่างประเทศ"),
            ("318104", "318104 - ธนาคารพาณิชย์ไทยปรับฐานะเงินตราต่างประเทศ"),
            ("318113", "318113 - เงินทดรองจ่ายต่างๆ จากต่างประเทศ"),
            ("318116", "318116 - เงินจ่ายล่วงหน้าค่าบริการต่างๆ จากต่างประเทศ"),
            ("318122", "318122 - เงินโอนชำระหนี้แล้วไม่ได้ชำระ โอนกลับ"),
            ("318123", "318123 - ส่งเงินสำรองเพื่อการชำระคืนเงินกู้ต่างประเทศ"),
            ("318125", "318125 - เงินทดรองจ่ายต่างๆ ในต่างประเทศ"),
            ("318128", "318128 - เงินจ่ายล่วงหน้าค่าบริการต่างๆ ในต่างประเทศ"),
            ("318131", "318131 - เงินทุนอื่น ๆ (โปรดระบุรายละเอียด)"),
            ("318143", "318143 - ถอนจากบัญชี FCD เพื่อขายรับบาท"),
            ("318144", "318144 - ย้ายเงินในบัญชี FCD ของตนเอง"),
            ("318167", "318167 - ตัวแทนโอนเงินระหว่างประเทศ"),
            ("318212", "318212 - เงินส่วนต่างตามธุรกรรมอนุพันธ์"),
            ("318213", "318213 - เงินลงทุนในหลักทรัพย์ต่างประเทศในต่างประเทศ"),
            ("318215", "318215 - บริษัทหลักทรัพย์รับอนุญาต"),
            ("318216", "318216 - เงินลงทุนในหลักทรัพย์ไทยในต่างประเทศ"),
            ("318219", "318219 - ซื้อเงินตราต่างประเทศฝากเข้า FCD - เพื่อค่าสินค้า"),
            ("318220", "318220 - ซื้อเงินตราต่างประเทศฝากเข้า FCD - เพื่อค่าบริการ"),
            ("318221", "318221 - ซื้อเงินตราต่างประเทศฝากเข้า FCD - เพื่อการลงทุน"),
            ("318222", "318222 - ซื้อเงินตราต่างประเทศฝากเข้า FCD - เพื่อการกู้ยืม"),
            (
                "318223",
                "318223 - ซื้อเงินตราต่างประเทศฝากเข้า FCD - เพื่อวัตถุประสงค์อื่น",
            ),
            (
                "318224",
                "318224 - ฝากเงินตราต่างประเทศกับสถาบันการเงินในต่างประเทศเพื่อการลงทุน"
                "ในหลักทรัพย์หรือเงินฝากเพื่อหาผลตอบแทน",
            ),
            (
                "318225",
                "318225 - ฝากเงินตราต่างประเทศ กับสถาบันการเงินในต่างประเทศ "
                "เพื่อวัตถุประสงค์อื่น",
            ),
            ("318231", "318231 - ค่าสินค้าเข้าและสินค้าออก"),
            (
                "318232",
                "318232 - ส่วนลด เงินมัดจำ เงินที่ชำระไว้เกิน และอื่นๆของค่าสินค้า",
            ),
            ("318233", "318233 - ค่าทองคำ"),
            ("318236", "318236 - ธุรกรรม market maker เพื่ออนุพันธ์ อ้างอิงราคาทองคำ"),
            ("318237", "318237 - ธุรกรรม market maker เพื่ออนุพันธ์อ้างอิงตัวแปรอื่น"),
            (
                "318239",
                "318239 - ย้ายเงินในบัญชี FCD ของศูนย์บริหารเงินกับกลุ่มบริษัทเพื่อการกู้ยืม",
            ),
            (
                "318240",
                "318240 - ย้ายเงินในบัญชี FCD ของศูนย์บริหารเงินกับกลุ่มบริษัท"
                "เพื่อค่าสินค้าและบริการ",
            ),
            (
                "318241",
                "318241 - ย้ายเงินในบัญชี FCD ของศูนย์บริหารเงินกับกลุ่มบริษัท"
                "เพื่อการซื้อขาย FX",
            ),
            (
                "318242",
                "318242 - ย้ายเงินในบัญชี FCD ของธุรกิจในเครือเพื่อวัตถุประสงค์อื่น",
            ),
            (
                "318243",
                "318243 - ย้ายเงินในบัญชี FCD ระหว่างบุคคลอื่นเพื่อค่าสินค้าและบริการ",
            ),
            (
                "318244",
                "318244 - ย้ายเงินในบัญชี FCD ระหว่างบุคคลอื่นเพื่อการลงทุนในหลักทรัพย์",
            ),
            (
                "318245",
                "318245 - ย้ายเงินในบัญชี FCD ระหว่างบุคคลอื่นเพื่อวัตถุประสงค์อื่น",
            ),
            ("318246", "318246 - อื่น ๆ (โปรดระบุรายละเอียด)"),
            ("318247", "318247 - ค่าบริการซ่อมบำรุงเครื่องจักรและอุปกรณ์"),
        ],
        string="Objective Code",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_objective_description = fields.Char(
        string="Objective Description",
        size=100,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_document_support = fields.Selection(
        selection=[
            ("01", "01 - Proforma Invoice"),
            ("02", "02 - Invoice"),
            ("03", "03 - Contract / Agreement"),
            ("04", "04 - Others"),
        ],
        string="Document Support",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_document_other = fields.Char(
        string="Document Other",
        size=35,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_commodity_code = fields.Selection(
        selection=[
            ("I21041", "I21041 - Wood,Lumber,Cork,Pulp,Waste Paper"),
            ("I12071", "I12071 - Small Arms"),
            ("I21061", "I21061 - Textile Yarn & Thread"),
            ("I21071", "I21071 - Fabrics"),
            ("I21081", "I21081 - Jewelry,Including Silver Bars"),
            ("I21051", "I21051 - Natural"),
            ("I21052", "I21052 - Synthetic"),
            ("I21091", "I21091 - Paper & PaperBoard"),
            ("I21101", "I21101 - Chemicals"),
            ("I22011", "I22011 - Crude Minerals"),
            ("I30031", "I30031 - Construction Materials"),
            ("I22021", "I22021 - Iron & Steel"),
            ("I22022", "I22022 - Others (Base Metals)"),
            ("I30011", "I30011 - Fertilizers & Pesticides"),
            ("I30021", "I30021 - Cement"),
            ("I30041", "I30041 - Tubes & Pipes"),
            ("I30051", "I30051 - Glass & Other Mineral Manufactures"),
            ("I30061", "I30061 - Rubber Manufactures"),
            ("I30071", "I30071 - Metal Manufactures"),
            ("I30081", "I30081 - Non-Elect.Mach.for Agricultural Use"),
            ("I30131", "I30131 - Computer"),
            ("I11014", "I11014 - Coffee, Tea & Spices"),
            ("I11015", "I11015 - Others (Food & Beverages)"),
            ("I30141", "I30141 - Computer Components"),
            ("I30082", "I30082 - Tractors"),
            ("I30083", "I30083 - Non-Elect.Mach.for Industrial Use"),
            ("I11011", "I11011 - Dairy Products"),
            ("I11012", "I11012 - Cereals & Preparations"),
            ("I11013", "I11013 - Fruits & Vegetables"),
            ("I11021", "I11021 - Tobacco Products"),
            ("I11031", "I11031 - Toilet & Cleaning Articles"),
            ("I11041", "I11041 - Clothing & Footwear"),
            ("I11051", "I11051 - Medicinal & Pharmaceutical Products"),
            ("I12011", "I12011 - Household Goods"),
            ("I12021", "I12021 - Electrical Appliances"),
            ("I12031", "I12031 - Wood & Cork Products"),
            ("I12041", "I12041 - Leather & Leather Products"),
            ("I12051", "I12051 - Furniture"),
            ("I12061", "I12061 - Cycles,Motorcycles,Carts,etc."),
            ("I21011", "I21011 - Fish and Preparations"),
            ("I21031", "I21031 - Tobacco Leaves"),
            ("I21021", "I21021 - Animal and vegetable crude materials"),
            ("I30091", "I30091 - Electrical Machinery and Parts"),
            ("I30101", "I30101 - Scientific & Optical Instruments"),
            ("I30111", "I30111 - Aircraft & Ships"),
            ("I30121", "I30121 - Locomotive & Rolling Stock"),
            ("I30151", "I30151 - Integrated circuits"),
            ("I30161", "I30161 - Integrated circuits components"),
            ("I40011", "I40011 - Passenger Cars"),
            ("I40012", "I40012 - Buses & Trucks"),
            ("I40013", "I40013 - Chassis & Bodies"),
            ("I40014", "I40014 - Tires"),
            ("I40015", "I40015 - Others (Vehicles and Parts)"),
            ("I40021", "I40021 - Coke,Briquettes,etc."),
            ("I40022", "I40022 - Crude Oil"),
            ("I40023", "I40023 - Gasoline"),
            ("I40024", "I40024 - Kerosene"),
            ("I40025", "I40025 - Diesel Oil & Special Fuels"),
            ("I40026", "I40026 - Lubricants,Asphalt,etc."),
            ("I40031", "I40031 - Munitions Used in Official Services"),
            ("I40032", "I40032 - Other (Miscellaneous)"),
            ("I40041", "I40041 - Gold Bullion"),
            ("I40051", "I40051 - Thai military imports"),
            ("I40061", "I40061 - Electricity imports"),
        ],
        string="Commodity Code",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_pre_advice = fields.Boolean(
        string="Pre-Advice",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_execution_date = fields.Date(
        string="Execution Date",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_intermediary_bank_id = fields.Many2one(
        comodel_name="res.bank",
        string="Intermediary Bank",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_intermediary_bank_account_number = fields.Char(
        string="Intermediary Bank Account Number",
        size=34,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_additional_instruction = fields.Char(
        string="Additional Instruction",
        size=350,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_product_code = fields.Selection(
        selection=[
            ("BNT", "BNT - Bahtnet"),
            ("DCP", "DCP - Direct Credit"),
            ("MCL", "MCL - Media Clearing"),
            ("PAY", "PAY - Payroll"),
            ("PA2", "PA2 - Payroll 2"),
            ("PA3", "PA3 - Payroll 3"),
            ("PA4", "PA4 - MediaClearing Payroll"),
            ("PA5", "PA5 - MediaClearing Payroll 2"),
            ("PA6", "PA6 - MediaClearing Payroll 3"),
            ("MCP", "MCP - MCheque"),
            ("CCP", "CCP - Corporate Cheque"),
            ("DDP", "DDP - Demand Draft"),
            ("XMQ", "XMQ - Express Manager Cheque"),
            ("XDQ", "XDQ - Express Demand Draft"),
        ],
        ondelete={
            "BNT": "cascade",
            "DCP": "cascade",
            "MCL": "cascade",
            "PAY": "cascade",
            "PA2": "cascade",
            "PA3": "cascade",
            "PA4": "cascade",
            "PA5": "cascade",
            "PA6": "cascade",
            "MCP": "cascade",
            "CCP": "cascade",
            "DDP": "cascade",
            "XMQ": "cascade",
            "XDQ": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_delivery_mode = fields.Selection(
        selection=[
            ("M", "M - Send by Registered mail"),
            ("C", "C - Send by messenger to Customer"),
            ("P", "P - Receiving pickup at SCB branch"),
            ("S", "S - Send back to SCBBusinessNet"),
        ],
        ondelete={
            "M": "cascade",
            "C": "cascade",
            "P": "cascade",
            "S": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_pickup_location = fields.Selection(
        selection=[
            ("C001", "C001 - รัชโยธิน"),
            ("C002", "C002 - ชิดลม"),
            ("C003", "C003 - มาบตาพุด"),
            ("C004", "C004 - ลาดกระบัง"),
            ("C005", "C005 - ท่าแพ"),
            ("C006", "C006 - อโศก"),
            ("C007", "C007 - พัทยา สาย2"),
            ("C008", "C008 - พระราม 4"),
            ("C009", "C009 - ถนนเชิดวุฒากาศ"),
            ("C010", "C010 - แหลมฉบัง"),
            ("C011", "C011 - ไอทีสแควร์ (หลักสี่)"),
            ("C012", "C012 - สุวรรณภูมิ"),
        ],
        ondelete={
            "C001": "cascade",
            "C002": "cascade",
            "C003": "cascade",
            "C004": "cascade",
            "C005": "cascade",
            "C006": "cascade",
            "C007": "cascade",
            "C008": "cascade",
            "C009": "cascade",
            "C010": "cascade",
            "C011": "cascade",
            "C012": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_pickup_location_cheque = fields.Selection(
        selection=[
            ("C002", "C002 - Ratchayothin (CAREER@SCB)-RCP"),
            ("C003", "C003 - Mab Ta Pud Industrial Estate br.0644"),
            ("C004", "C004 - By Return - รับเช็คที่บริษัท"),
            ("C005", "C005 - Phuket br.0537"),
            ("C006", "C006 - Asok br.0032"),
            ("C007", "C007 - Chachoengsao br.0516"),
            ("C008", "C008 - Phra Ram IV (Sirinrat Building) br.0096"),
            ("C009", "C009 - Thanon Cherd Wutthakat (Don Muang) br.0105"),
            ("C010", "C010 - Laem Chabang br.0807 LAEM CHABANG INDUSTRIAL ESTATE SUB"),
            ("C011", "C011 - By Mailing -ส่งทางไปรษณีย์"),
            ("C012", "C012 - ลาดกระบัง"),
            ("0111", "0111 - Ratchayothin West A"),
            ("5190", "5190 - Energy Complex"),
            ("5453", "5453 - G Tower"),
            ("0870", "0870 - Amata City (Rayong) Sub Br."),
            ("0101", "0101 - Thanon Sathon"),
            ("0527", "0527 - Sri Racha"),
        ],
        ondelete={
            "C002": "cascade",
            "C003": "cascade",
            "C004": "cascade",
            "C005": "cascade",
            "C006": "cascade",
            "C007": "cascade",
            "C008": "cascade",
            "C009": "cascade",
            "C010": "cascade",
            "C011": "cascade",
            "C012": "cascade",
            "0111": "cascade",
            "5190": "cascade",
            "5453": "cascade",
            "0870": "cascade",
            "0101": "cascade",
            "0527": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_service_type = fields.Selection(
        selection=[
            ("01", "01 - เงินเดือน, ค่าจ้าง, บำเหน็จ, บำนาญ"),
            ("02", "02 - เงินปันผล"),
            ("03", "03 - ดอกเบี้ย"),
            ("04", "04 - ค่าสินค้า, บริการ"),
            ("05", "05 - ขายหลักทรัพย์"),
            ("06", "06 - คืนภาษี"),
            ("07", "07 - เงินกู้"),
            ("59", "59 - อื่น ๆ"),
        ],
        ondelete={
            "01": "cascade",
            "02": "cascade",
            "03": "cascade",
            "04": "cascade",
            "05": "cascade",
            "06": "cascade",
            "07": "cascade",
            "59": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_service_type_bahtnet = fields.Selection(
        selection=[
            ("00", "00 - Other"),
            ("01", "01 - Freight"),
            ("02", "02 - Insurance Premium"),
            ("03", "03 - Trasportation Cost"),
            ("04", "04 - Travelling Expenses (Thai)"),
            ("05", "05 - Forign Tourist Expenses"),
            ("06", "06 - Interest Paid"),
            ("07", "07 - Dividened"),
            ("08", "08 - Education"),
            ("09", "09 - Royalty Fee"),
            ("10", "10 - Agency Expenses"),
            ("11", "11 - Advertising Fee"),
            ("12", "12 - Communication Cost"),
            ("13", "13 - Personal Remittance / Family Support"),
            ("14", "14 - Money Transfer for Government"),
            ("15", "15 - Embassy / Military / Government Expenses"),
            ("16", "16 - Thai Lobour Money Transfer"),
            ("17", "17 - Salary"),
            ("18", "18 - Commission Fee"),
            ("19", "19 - Loan"),
            ("20", "20 - Direct Investment"),
            ("21", "21 - Portfolio Investment"),
            ("22", "22 - Trade Transaction"),
            ("23", "23 - Fixed Asset Investment"),
        ],
        ondelete={
            "00": "cascade",
            "01": "cascade",
            "02": "cascade",
            "03": "cascade",
            "04": "cascade",
            "05": "cascade",
            "06": "cascade",
            "07": "cascade",
            "08": "cascade",
            "09": "cascade",
            "10": "cascade",
            "11": "cascade",
            "12": "cascade",
            "13": "cascade",
            "14": "cascade",
            "15": "cascade",
            "16": "cascade",
            "17": "cascade",
            "18": "cascade",
            "19": "cascade",
            "20": "cascade",
            "21": "cascade",
            "22": "cascade",
            "23": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_invoice_language = fields.Selection(
        selection=[("T", "T - Thai"), ("E", "E - English")],
        ondelete={
            "T": "cascade",
            "E": "cascade",
        },
        default="T",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_is_invoice_present = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_is_wht_present = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_is_credit_advice = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_wht_signatory = fields.Selection(
        selection=[("B", "B - Bank"), ("C", "C - Corporate")],
        ondelete={
            "B": "cascade",
            "C": "cascade",
        },
        default="B",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_beneficiary_charge = fields.Boolean(
        string="Beneficiary Charge",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_cheque_ref = fields.Selection(
        selection=[
            ("1", "1 - ใบเสร็จรับเงิน"),
            ("2", "2 - ใบวางบิล"),
            ("3", "3 - ใบเสร็จรับเงินและใบวางบิล"),
            ("4", "4 - ใบเสร็จรับเงินและใบกำกับภาษี"),
            ("5", "5 - ใบวางบิลและใบเสร็จรับเงินและใบกำกับภาษี"),
            ("6", "6 - สำเนาบัตรประชาชน/หนังสือเดินทาง"),
            ("7", "7 - สำเนาบัตรประชาชน/หนังสือเดินทาง + ใบนัดรับของรางวัล"),
            ("8", "8 - สำเนาบัตรประชาชน/หนังสือเดินทาง + ใบสั่งจ้าง"),
            ("9", "9 - สำเนาใบเสร็จรับเงิน"),
            ("A", "A - เงินในเช็คใบเสร็จไม่เท่ากัน - จ่าย"),
            ("B", "B - หนังสือรับรองการหักภาษีณ.ที่จ่าย."),
            ("C", "C - หนังสือกรมศุลกากร"),
            ("D", "D - ใบกำกับภาษี"),
            (
                "E",
                "E - หนังสือมอบพร้อมติดอากรแสตมป์ 10 บาท + สำเนาบัตร ปชช.ผู้มอบพร้อมลงนาม "
                "+ สำเนาบัตร ปชช.ผู้รับมอบพร้อมลงนาม",
            ),
            (
                "F",
                "F - หนังสือมอบจากคณะบุคคลพร้อมติดอากรแสตมป์ 10 บาท + "
                "สำเนาสัญญาจัดตั้งคณะบุคคลพร้อมลงนาม + "
                "สำเนาบัตรผู้เสียภาษีของคณะบุคคลพร้อมลงนาม + "
                "สำเนาบัตร ปชช.ผู้มอบ และผู้รับมอบ พร้อมลงนาม",
            ),
            ("G", "G - เอกสารยืนยันการโอนเงิน/ออกเช็คผ่านโทรสาร"),
            ("H", "H - อื่น ๆ"),
            ("I", "I - สัญญาประนีประนอม"),
            ("J", "J - ใบเสร็จ/ใบกำกับภาษี + ใบรับรถ"),
            ("K", "K - หนังสือมอบ + บัตร ปชช.ผู้รับมอบ"),
            ("L", "L - บัตร ปชช.ผู้มอบ + บัตร ปชช.ผู้รับมอบ"),
            ("M", "M - ใบรับรถ + เซ็นชื่อใบรับเงิน/สัญญา"),
            ("N", "N - ใบรถ + น.มอบ + ผู้รับมอบ + เซ็นชื่อ/สัญญา"),
            ("O", "O - ใบรับเช็ค"),
            ("P", "P - ใบลดหนี้"),
            ("Q", "Q - ใบเพิ่มหนี้"),
            ("R", "R - ดูช่อง Invoice Description ใน Advice"),
            ("S", "S - ขายลดเช็คทันที"),
            ("T", "T - Email + สำเนาบัตรพนง. + สำเนาบัตรปปช."),
            ("U", "U - ค่าสาธารณูปโภค"),
            ("V", "V - ใบเสร็จรับเงินและ หนังสือรับรองหักภาษี ณ ที่จ่าย"),
            ("W", "W - ใบเสร็จรับเงิน หรือบัตรประชาชน"),
            ("X", "X - ไม่ใช้เอกสารใด ๆ"),
            ("Y", "Y - ใบวางบิลและใบเสร็จรับเงิน (จำนวนเงินไม่ตรง-จ่าย)"),
            ("Z", "Z - ใบวางบิลและสำเนาบัตรประชาชน"),
        ],
        ondelete={
            "1": "cascade",
            "2": "cascade",
            "3": "cascade",
            "4": "cascade",
            "5": "cascade",
            "6": "cascade",
            "7": "cascade",
            "8": "cascade",
            "9": "cascade",
            "A": "cascade",
            "B": "cascade",
            "C": "cascade",
            "D": "cascade",
            "E": "cascade",
            "F": "cascade",
            "G": "cascade",
            "H": "cascade",
            "I": "cascade",
            "J": "cascade",
            "K": "cascade",
            "L": "cascade",
            "M": "cascade",
            "N": "cascade",
            "O": "cascade",
            "P": "cascade",
            "Q": "cascade",
            "R": "cascade",
            "S": "cascade",
            "T": "cascade",
            "U": "cascade",
            "V": "cascade",
            "W": "cascade",
            "X": "cascade",
            "Y": "cascade",
            "Z": "cascade",
        },
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_remark = fields.Char(
        string="Remark",
        size=50,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    scb_payment_type_code = fields.Selection(
        selection=[
            ("CSH", "CSH - Cash"),
            ("BCQ", "BCQ - Branch or other bank chqs"),
            ("HCQ", "HCQ - Home chqs"),
            ("DCA", "DCA - Current A/C"),
            ("DSA", "DSA - Saving A/C"),
            ("BCA", "BCA - Current A/C - other branch"),
            ("BSA", "BSA - Saving A/C - other branch"),
            ("FCA", "FCA - Foreign cur. Current A/C"),
            ("FSA", "FSA - Foreign cur. Saving A/C"),
            ("SPD", "SPD - Suspense debtor"),
            ("SPC", "SPC - Suspense creditor"),
            ("UST", "UST - Unsettled"),
            ("OFA", "OFA - Offline Account"),
            ("FWD", "FWD - Forward Value"),
        ],
        ondelete={
            "CSH": "cascade",
            "BCQ": "cascade",
            "HCQ": "cascade",
            "DCA": "cascade",
            "DSA": "cascade",
            "BCA": "cascade",
            "BSA": "cascade",
            "FCA": "cascade",
            "FSA": "cascade",
            "SPD": "cascade",
            "SPC": "cascade",
            "UST": "cascade",
            "OFA": "cascade",
            "FWD": "cascade",
        },
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.depends("bank")
    def _compute_required_effective_date(self):
        res = super()._compute_required_effective_date()
        for rec in self.filtered(lambda l: l.bank == "SICOTHBK"):
            rec.is_required_effective_date = True
        return res

    @api.depends("bank")
    def _compute_scb_editable(self):
        for export in self:
            export.scb_is_editable = True if export.bank == "SICOTHBK" else False

    @api.constrains("scb_execution_date")
    def check_scb_execution_date(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.scb_execution_date and not (
                today <= rec.scb_execution_date <= rec.effective_date
            ):
                raise UserError(
                    _("Execution Date must be within %(date_from)s to %(date_to)s")
                    % {
                        "date_from": today.strftime("%d/%m/%Y"),
                        "date_to": rec.effective_date.strftime("%d/%m/%Y"),
                    }
                )

    def _get_scb_amount_no_decimal(self, amount, digits=16, is_round=True):
        if is_round:
            amount = round(amount, 2)
        return str(int(Decimal(str(amount)) * 1000)).zfill(digits)

    def _get_reference(self):
        return self.name

    def _get_batch_reference(self):
        return self.name

    def _get_line_count(self, payment_lines):
        return len(payment_lines)

    def _get_mcl_type(self):
        if self.scb_product_code == "MCL" and self.scb_bank_type == "2":
            return "2"
        return " "

    def _get_payee_name_eng(self, pe_line, receiver_name=""):
        if self.scb_product_code == "BNT":
            receiver_name = (
                pe_line.payment_partner_bank_id.acc_holder_name_en
                or "**Not found account holder en**"
            )
            return receiver_name
        return receiver_name

    def _get_wht_income_type(self, wht_line):
        wht_income_type = wht_line.wht_cert_income_type.lower()
        if len(wht_income_type) == 4:
            wht_income_type = "{}.{}".format(wht_income_type[:3], wht_income_type[3:])
        return wht_income_type

    def _get_wht_header(self, wht_cert):
        wht_type = "00"
        if not (wht_cert and self.scb_is_wht_present):
            return "{wht_type}{filter}{filter_number}".format(
                wht_type=wht_type,
                filter="".ljust(14),
                filter_number="0".zfill(24),
            )
        if wht_cert.income_tax_form == "pnd1":
            wht_type = "01"
        elif wht_cert.income_tax_form == "pnd3":
            wht_type = "03"
        elif wht_cert.income_tax_form == "pnd53":
            wht_type = "53"
        total_wht = self._get_scb_amount_no_decimal(
            sum(wht_cert.wht_line.mapped("amount"))
        )
        text = "{wht_type}{wht_running_no}{wht_attach_no}{wht_line}{total_wht}".format(
            wht_type=wht_type,  # 70-71
            # NOTE: Bank will generate
            wht_running_no="".ljust(14),  # 72-85
            # NOTE: Bank will generate
            wht_attach_no="0".zfill(6),  # 86-91
            wht_line=str(len(wht_cert.wht_line)).zfill(2),  # 92-93
            total_wht=total_wht,  # 94-109
        )
        return text

    def _get_wht_header2(self, wht_cert):
        if not (wht_cert and self.scb_is_wht_present):
            return "0{}".format("".ljust(48))
        mapping_tax_payer = {
            "withholding": "3",
            "paid_one_time": "1",
        }
        text = "{pay_type}{wht_remark}{wht_deduct_date}".format(
            pay_type=mapping_tax_payer.get(wht_cert.tax_payer),  # 132-132
            # NOTE: System is not type 4
            wht_remark="".ljust(40),  # 133-172
            wht_deduct_date=wht_cert.date.strftime("%Y%m%d"),  # 173-180
        )
        return text

    def _get_invoice_header(self, invoices):
        if not self.scb_is_invoice_present:
            return "0".zfill(22)
        invoice_total_amount = self._get_scb_amount_no_decimal(
            sum(invoices.mapped("amount_total"))
        )
        text = "{invoice_count}{invoice_total_amount}".format(
            invoice_count=str(len(invoices)).zfill(6),  # 110-115
            invoice_total_amount=invoice_total_amount,  # 116-131
        )
        return text

    def _get_pickup_location(self):
        pickup = ""
        if self.scb_product_code in ["MCP", "CCP", "DDP", "XMQ", "XDQ"]:
            if self.scb_delivery_mode in ["C", "P"]:
                pickup = self.scb_pickup_location_cheque
        else:
            if self.scb_delivery_mode == "C":
                pickup = self.scb_pickup_location
        return pickup.ljust(4)

    def _get_scb_bank_name(self, receiver_bank_name):
        # NOTE: Not support thai language
        return (receiver_bank_name and receiver_bank_name[:35] or "").ljust(35)

    def _get_service_type(self):
        if self.scb_product_code == "BNT":
            return self.scb_service_type_bahtnet
        return self.scb_service_type

    def _get_address(self, object_address, max_length):
        if self.scb_product_code == "BNT" or self.scb_outward_remittance:
            receiver_address = object_address.street3 or "**street3 is not data**"
        else:
            receiver_address = " ".join(
                [
                    object_address.street or "",
                    object_address.street2 or "",
                    object_address.city or "",
                    object_address.zip or "",
                ]
            )

        def split_thai_string(input_string, max_length):
            words = input_string.split()
            result = []
            current_line = ""

            for word in words:
                if len(current_line + word) > max_length:
                    result.append(current_line.strip())
                    current_line = ""

                current_line += word + " "

            if current_line.strip():
                result.append(current_line.strip())

            return result

        def pad_lines(lines, desired_length):
            padded_lines = [line.ljust(desired_length) for line in lines]
            return padded_lines

        def ensure_three_lines(lines, desired_length):
            while len(lines) < 3:
                lines.append("".ljust(desired_length))

        result = split_thai_string(receiver_address, max_length)
        padded_result = pad_lines(result, max_length)
        ensure_three_lines(padded_result, max_length)

        return "".join(padded_result)

    def _get_scb_payment_details(self, payment_lines):
        """Can hooks this function for more payment details (limit 140 char)"""
        return payment_lines[0].payment_id.name.ljust(140)

    def _get_text_header_scb(self):
        self.ensure_one()
        scb_company_id = self.scb_company_id or "**Company ID on SCB is not config**"
        today = fields.Datetime.context_timestamp(self.env.user, datetime.now())
        file_date = today.strftime("%Y%m%d")
        file_time = today.strftime("%H%M%S")
        text = (
            "001{scb_company}{customer_ref}{file_date}{file_time}{channel_id}"
            "{batch_reference}\r\n".format(
                scb_company=scb_company_id.ljust(12),  # 4-15
                customer_ref=self._get_reference().ljust(32),  # 16-47
                file_date=file_date,  # 48-55
                file_time=file_time,  # 56-61
                channel_id="BCM",  # 62-64
                batch_reference=self._get_reference().ljust(32),  # 65-96
            )
        )
        return text

    def _get_text_company_detail_scb(self, payment_lines, total_batch_amount, idx=1):
        self.ensure_one()
        # NOTE: Can pay with 1 account
        account_bank_payment = payment_lines[
            0
        ].payment_journal_id.bank_account_id.acc_number
        sanitize_account_bank_payment = sanitize_account_number(account_bank_payment)
        if not sanitize_account_bank_payment:
            sanitize_account_bank_payment = "-----------"  # default 11 digits
        account_type = "0{}".format(sanitize_account_bank_payment[3])
        branch_code = "0{}".format(sanitize_account_bank_payment[0:3])
        text = (
            "002{product_code}{value_date}{debit_account_no}{account_type_debit_account}"
            "{debit_branch_code}{currency_name}{debit_amount}{internal_ref}{no_credit}"
            "{debit_fee_account}{filler}{mcl_type}{account_type_fee}"
            "{debit_fee_branch_code}\r\n".format(
                product_code=self.scb_product_code,  # 4-6
                value_date=self.effective_date.strftime("%Y%m%d"),  # 7-14
                debit_account_no=sanitize_account_bank_payment.ljust(25),  # 15-39
                account_type_debit_account=account_type,  # 40-41
                debit_branch_code=branch_code,  # 42-45
                currency_name="THB",  # 46-48
                debit_amount=total_batch_amount,  # 49-64
                internal_ref=str(idx).zfill(8),  # 65-72
                no_credit=str(self._get_line_count(payment_lines)).zfill(6),  # 73-78
                debit_fee_account=sanitize_account_bank_payment.ljust(15),  # 79-93
                filler="".ljust(9),  # 94-102
                mcl_type=self._get_mcl_type(),  # 103-103
                account_type_fee=account_type.zfill(2),  # 104-105
                debit_fee_branch_code=branch_code.zfill(4),  # 106-109
            )
        )
        return text, idx

    def _get_text_credit_detail_scb(
        self, idx, pe_line, line_batch_amount, wht_cert, invoices, internal_ref
    ):
        # Receiver
        (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        ) = pe_line._get_receiver_information()
        receiver_bank_name = pe_line.payment_partner_bank_id.bank_id.name
        if self.scb_product_code in ["MCP", "CCP", "DDP", "XMQ", "XDQ", "DCP"]:
            receiver_bank_code = "014"
            receiver_bank_name = "SCB"
            receiver_branch_code = "0111"
            # Direct Cheque don't use account number
            if self.scb_product_code != "DCP":
                receiver_acc_number = ""
        text = (
            "003{idx}{credit_account}{credit_amount}{currency_name}{internal_ref}{wht_present}"
            "{invoice_detail_present}{credit_advice_required}{delivery_mode}"
            "{pickup_location}{wht_header}{invoice_number}{wht_header2}"
            "{receiver_bank_code}{receiver_bank_name}{receiver_branch_code}"
            "{receiver_branch_name}{wht_signatory}{notification}{customer_ref}"
            "{cheque_ref}{payment_type_code}{service_type}{remark}"
            "{scb_remark}{charge}\r\n".format(
                idx=str(idx).zfill(6),  # 4-9
                credit_account=receiver_acc_number.ljust(25),  # 10-34
                credit_amount=line_batch_amount,  # 35-50
                currency_name="THB",  # 51-53
                internal_ref=str(internal_ref).zfill(8),  # 54-61
                wht_present="Y"
                if self.scb_is_wht_present and wht_cert
                else "N",  # 62-62
                invoice_detail_present="Y"  # 63-63
                if self.scb_is_invoice_present and invoices
                else "N",
                credit_advice_required="Y"
                if self.scb_is_credit_advice
                else "N",  # 64-64
                delivery_mode=self.scb_delivery_mode or " ",  # 65-65
                pickup_location=self._get_pickup_location(),  # 66-69
                wht_header=self._get_wht_header(wht_cert),  # 70-109
                invoice_number=self._get_invoice_header(invoices),  # 110-131
                wht_header2=self._get_wht_header2(wht_cert),  # 132-180
                receiver_bank_code=receiver_bank_code,  # 181-183
                receiver_bank_name=self._get_scb_bank_name(
                    receiver_bank_name
                ),  # 184-218
                receiver_branch_code=receiver_branch_code,  # 219-222
                receiver_branch_name=(receiver_branch_code or "").ljust(35),  # 223-257
                wht_signatory=self.scb_wht_signatory,  # 258-258
                notification=pe_line.scb_beneficiary_noti,  # 259-259
                customer_ref=pe_line.payment_id.name.ljust(20),  # 260-279
                cheque_ref=self.scb_cheque_ref or "".ljust(1),  # 280-280
                payment_type_code=self.scb_payment_type_code or "".ljust(3),  # 281-283
                service_type=self._get_service_type() or "".ljust(2),  # 284-285
                remark=(self.scb_remark or "").ljust(50),  # 286-335
                scb_remark="".ljust(18),  # 336-353
                charge="B " if pe_line.scb_beneficiary_charge else "  ",  # 354-355
            )
        )
        return text

    def _get_text_payee_detail_scb(self, idx, pe_line, line_batch_amount, internal_ref):
        receiver_name = pe_line._get_receiver_information()[0]
        # For case cheque get name from payee name
        if self.scb_product_code in ["MCP", "CCP", "DDP", "XMQ", "XDQ"]:
            receiver_name = pe_line.payment_id.check_payee
        address = self._get_address(pe_line.payment_partner_id, 70)
        text = (
            "004{internal_ref}{idx}{payee_idcard}{payee_name}"
            "{payee_address}{payee_tax_id}{payee_name_eng}{payee_fax}{payee_sms}"
            "{payee_email}{space}\r\n".format(
                internal_ref=str(internal_ref).zfill(8),  # 4-11
                idx=str(idx).zfill(6),  # 12-17
                payee_idcard=str(pe_line.payment_partner_id.vat or "").ljust(
                    15
                ),  # 18-32
                payee_name=receiver_name.ljust(100),  # 33-132
                payee_address=address,  # 133-342
                payee_tax_id="".ljust(10),  # 343-352
                payee_name_eng=self._get_payee_name_eng(pe_line).ljust(70),  # 353-422
                payee_fax=pe_line._get_payee_fax().zfill(10),  # 423-432
                payee_sms=pe_line._get_payee_sms().zfill(10),  # 433-442
                payee_email=(pe_line._get_payee_email() or "").ljust(64),  # 443-506
                # TODO Payee2 do not implement yet.
                space="".ljust(310),  # 507-816
            )
        )
        return text

    def _get_text_wht_detail_scb(self, idx, sequence_wht, wht_line, internal_ref):
        wht_amount = self._get_scb_amount_no_decimal(wht_line.amount)
        wht_base_amount = self._get_scb_amount_no_decimal(wht_line.base)
        wht_income_type = self._get_wht_income_type(wht_line)
        text = (
            "005{internal_ref}{idx}{wht_sequence}{wht_amount}"
            "{wht_income_type}{wht_income_description}{wht_deduct_rate}"
            "{wht_base_amount}\r\n".format(
                internal_ref=str(internal_ref).zfill(8),  # 4-11
                idx=str(idx).zfill(6),  # 12-17
                wht_sequence=str(sequence_wht).zfill(2),  # 18-19
                wht_amount=wht_amount,  # 20-35
                wht_income_type=wht_income_type.ljust(5),  # 36-40
                wht_income_description=wht_line.wht_cert_income_desc.ljust(
                    80
                ),  # 41-120
                wht_deduct_rate=str(abs(int(wht_line.wht_percent))).zfill(2),  # 121-122
                wht_base_amount=wht_base_amount,  # 123-138
            )
        )
        return text

    def _get_text_invoice_detail_scb(
        self, idx, sequence_inv, inv, pe_line, internal_ref
    ):
        inv_amount_untaxed = self._get_scb_amount_no_decimal(inv.amount_untaxed)
        inv_amount_tax = self._get_scb_amount_no_decimal(inv.amount_tax)
        # Check install module purchase
        purchase = False
        if hasattr(inv.invoice_line_ids, "purchase_line_id"):
            purchase = inv.invoice_line_ids.mapped("purchase_line_id.order_id")
        # Check install module l10n_th_account_tax (not required)
        wht_lines = False
        amount_wht = 0.0
        if hasattr(inv.invoice_line_ids, "wht_tax_id"):
            wht_lines = inv.invoice_line_ids.filtered("wht_tax_id")
            amount_wht = wht_lines._get_wht_amount(
                self.env.company.currency_id, pe_line.payment_date
            )[1]
        amount_wht = self._get_scb_amount_no_decimal(amount_wht)
        text = (
            "006{internal_ref}{idx}{inv_sequence}{inv_number}{inv_amount}"
            "{inv_date}{inv_description}{po_number}{vat_amount}{payee_chage_amount}"
            "{wht_amount}{language}\r\n".format(
                internal_ref=str(internal_ref).zfill(8),  # 4-11
                idx=str(idx).zfill(6),  # 12-17
                inv_sequence=str(sequence_inv).zfill(6),  # 18-23
                inv_number=inv.name.ljust(15)
                if inv.name != "/"
                else ".".ljust(15),  # 24-38
                inv_amount=inv_amount_untaxed,  # 39-54
                inv_date=inv.invoice_date.strftime("%Y%m%d"),  # 55-62
                inv_description="".ljust(70),  # 63-132
                po_number=(purchase and purchase.name or "").ljust(15),  # 133-147
                vat_amount=inv_amount_tax,  # 148-163
                payee_chage_amount="0".zfill(16),  # 164-179
                wht_amount=amount_wht,  # 180-195
                language=self.scb_invoice_language,  # 196-196
            )
        )
        return text

    def _get_text_footer_scb(self, payment_lines, total_batch_amount, internal_ref):
        text = "999{total_debit}{total_credit}{total_amount}\r\n".format(
            total_debit=str(internal_ref).zfill(6),  # 4-9
            total_credit=str(len(payment_lines)).zfill(6),  # 10-15
            total_amount=total_batch_amount,  # 16-31
        )
        return text

    def _get_text_outward_remittance(self, payment_lines):
        self.ensure_one()
        account_bank_payment = payment_lines[
            0
        ].payment_journal_id.bank_account_id.acc_number
        sanitize_account_bank_payment = sanitize_account_number(account_bank_payment)
        formatted_string = f"{self.scb_rate:.7f}"
        integer_part, decimal_part = formatted_string.split(".")
        # Ensure the integer part has exactly three digits
        integer_part = integer_part.zfill(3)
        rate = f"{integer_part}.{decimal_part}"
        # Total Amount must have lenght 17 and digits at least 2
        total_amount = str(self.total_amount).zfill(17)
        integer_part_total, decimal_part_total = str(self.total_amount).split(".")
        if len(decimal_part_total) < 2:
            decimal_part_total = decimal_part_total.zfill(2)
        total_amount = f"{integer_part_total}.{decimal_part_total}".zfill(17)
        partner_bank_id = payment_lines[0].payment_partner_bank_id
        # Get Receiver information
        receiver_name = (
            partner_bank_id.acc_holder_name_en
            or partner_bank_id.acc_holder_name
            or partner_bank_id.partner_id.display_name
        )
        receiver_acc_number = sanitize_account_number(partner_bank_id.acc_number)
        receiver_address = self._get_address(payment_lines[0].payment_partner_id, 35)
        # Get bank information
        bank_name = partner_bank_id.bank_id.name
        bank_address = self._get_address(partner_bank_id.bank_id, 35)
        execution_date = (
            self.scb_execution_date
            and self.scb_execution_date.strftime("%Y%m%d")
            or "".ljust(8)
        )
        intermediary_bank_address = self._get_address(self.scb_intermediary_bank_id, 35)

        text = (
            "{transaction_number}{batch_reference}{corp_id}{for_id}{value_date}"
            "{debit_account_no}{debit_fee_account}{rate_type}{contract_ref_no}{rate}"
            "{credit_currency}{credit_amount}{beneficiary_name}{beneficiary_address}"
            "{beneficiary_account}{beneficiary_bank_name}{beneficiary_bank_address}"
            "{charge_flag}{objective_code}{objective_description}{payment_details}"
            "{document_support}{document_other}{commodity_code}{customer_reference1}"
            "{customer_reference2}{filler}{pre_advice}{beneficiary_email}"
            "{execution_date}{intermediary_bank_account}{intermediary_bank_name}"
            "{intermediary_bank_address}{additional_instruction}{debit_amount}"
            "{debit_account_addons}{filler2}".format(
                transaction_number="000001",  # TODO
                batch_reference=self._get_batch_reference().ljust(32),
                corp_id=(self.scb_corp_id or "").ljust(12),
                for_id=(self.scb_for_id or "").ljust(20),
                value_date=self.effective_date.strftime("%Y%m%d"),
                debit_account_no=(sanitize_account_bank_payment or "").ljust(35),
                debit_fee_account=(sanitize_account_bank_payment or "").ljust(35),
                rate_type=self.scb_rate_type,
                contract_ref_no=(self.scb_contract_ref_no or "").ljust(20),
                rate=rate,
                credit_currency=payment_lines[0].currency_id.name,
                credit_amount=total_amount,
                beneficiary_name=receiver_name.ljust(35),
                beneficiary_address=receiver_address,
                beneficiary_account=receiver_acc_number.ljust(34),
                beneficiary_bank_name=bank_name[:35].ljust(35),
                beneficiary_bank_address=bank_address,
                charge_flag=self.scb_charge_flag,
                objective_code=self.scb_objective_code,
                objective_description=(self.scb_objective_description or "").ljust(100),
                payment_details=self._get_scb_payment_details(payment_lines),
                document_support=self.scb_document_support,
                document_other=(self.scb_document_other or "").ljust(35),
                commodity_code=(self.scb_commodity_code or "").ljust(6),
                customer_reference1=(payment_lines[0].scb_customer_ref1 or "").ljust(
                    32
                ),
                customer_reference2=(payment_lines[0].scb_customer_ref2 or "").ljust(
                    32
                ),
                filler="".ljust(220),  # 870-1089
                pre_advice=self.scb_pre_advice and "Y" or "N",
                beneficiary_email=(payment_lines[0].scb_beneficiary_email or "").ljust(
                    200
                ),
                execution_date=execution_date,
                intermediary_bank_account=(
                    self.scb_intermediary_bank_account_number or ""
                ).ljust(34),
                intermediary_bank_name=(
                    self.scb_intermediary_bank_id.bic
                    or self.scb_intermediary_bank_id.name
                    or ""
                ).ljust(35),
                intermediary_bank_address=intermediary_bank_address,
                additional_instruction=(self.scb_additional_instruction or "").ljust(
                    350
                ),
                debit_amount=total_amount,
                debit_account_addons="".ljust(156),  # NOTE: not support
                filler2="".ljust(505),  # NOTE: Include Beneficiary Fullname
            )
        )
        return text

    def _format_scb_text(self):
        self.ensure_one()
        payment_lines = self.export_line_ids
        # Outward Remittance
        if self.scb_outward_remittance:
            text = self._get_text_outward_remittance(payment_lines)
        else:
            # Header (001)
            text = self._get_text_header_scb()
            total_batch_amount = self._get_scb_amount_no_decimal(self.total_amount)
            # Debit Side for not BahtNet (002)
            if self.scb_product_code != "BNT":
                debit_text, internal_ref = self._get_text_company_detail_scb(
                    payment_lines, total_batch_amount
                )
                text += debit_text
            # Check module install 'l10n_th_account_tax'
            wht = hasattr(self.env["account.payment"], "wht_cert_ids")
            # Details
            for idx, pe_line in enumerate(payment_lines):
                idx += 1
                # Debit Side for BahtNet (002)
                if self.scb_product_code == "BNT":
                    payment_amount = self._get_scb_amount_no_decimal(
                        pe_line.payment_amount
                    )
                    debit_text, internal_ref = self._get_text_company_detail_scb(
                        pe_line, payment_amount, idx=idx
                    )
                    text += debit_text
                # This amount related decimal from invoice, Odoo invoice do not rounding.
                payment_net_amount = pe_line._get_payment_net_amount()
                line_batch_amount = pe_line._get_scb_amount_no_decimal(
                    payment_net_amount
                )
                wht_cert = (
                    wht
                    and pe_line.payment_id.wht_cert_ids.filtered(
                        lambda l: l.state == "done"
                    )
                    or False
                )
                invoices = pe_line.payment_id.reconciled_bill_ids
                # Credit Side (003)
                text += self._get_text_credit_detail_scb(
                    idx, pe_line, line_batch_amount, wht_cert, invoices, internal_ref
                )
                # Payee Detail (004)
                text += self._get_text_payee_detail_scb(
                    idx, pe_line, line_batch_amount, internal_ref
                )
                # Print WHT from bank
                if self.scb_is_wht_present and wht_cert:
                    # Get withholding tax from payment state done only
                    for sequence_wht, wht_line in enumerate(wht_cert.wht_line):
                        sequence_wht += 1
                        # Withholding Tax (005)
                        text += self._get_text_wht_detail_scb(
                            idx, sequence_wht, wht_line, internal_ref
                        )
                # Print Invoices from bank
                if self.scb_is_invoice_present:
                    for sequence_inv, inv in enumerate(invoices):
                        sequence_inv += 1
                        # Invoice Detail (006)
                        text += self._get_text_invoice_detail_scb(
                            idx, sequence_inv, inv, pe_line, internal_ref
                        )
            # Footer (999)
            text += self._get_text_footer_scb(
                payment_lines, total_batch_amount, internal_ref
            )
        return text

    def _generate_bank_payment_text(self):
        self.ensure_one()
        if self.bank == "SICOTHBK":  # SCB
            return self._format_scb_text()
        return super()._generate_bank_payment_text()

    def _get_view_report_text(self):
        """NOTE: This function can used demo. May be we delete it later"""
        if self.bank == "SICOTHBK":
            return "l10n_th_bank_payment_export_scb.action_payment_scb_txt"
        return super()._get_view_report_text()

    @api.onchange("scb_delivery_mode")
    def onchange_scb_delivery_mode(self):
        if self.scb_delivery_mode == "S" and self.scb_product_code in [
            "MCP",
            "DDP",
            "CCP",
        ]:
            raise UserError(
                _(
                    "The product codes 'MCP', 'DDP', and 'CCP' are not allowed "
                    "to be used with the 'SCBBusinessNet' delivery mode."
                )
            )

    def _check_constraint_confirm(self):
        res = super()._check_constraint_confirm()
        for rec in self.filtered(lambda l: l.bank == "SICOTHBK"):
            rec.onchange_scb_delivery_mode()
            if rec.scb_product_code == "DCP" and any(
                len(sanitize_account_number(line.payment_partner_bank_id.acc_number))
                != 10
                for line in rec.export_line_ids
            ):
                raise UserError(_("Account Number must only be 10 digits."))
        return res

    def _check_constraint_line(self):
        # Add condition with line on this function
        res = super()._check_constraint_line()
        self.ensure_one()
        if self.bank == "SICOTHBK":
            for line in self.export_line_ids:
                # Not cheque must select recipient bank
                if (
                    self.scb_product_code
                    not in [
                        "MCP",
                        "CCP",
                        "DDP",
                        "XMQ",
                        "XDQ",
                    ]
                    and not line.payment_partner_bank_id
                ):
                    raise UserError(
                        _("Recipient Bank with %(payment)s is not selected.")
                        % {
                            "payment": line.payment_id.name,
                        }
                    )
                if (
                    not self.scb_outward_remittance
                    and line.scb_beneficiary_email
                    and len(line.scb_beneficiary_email) > 64
                ):
                    raise UserError(
                        _(
                            "The length of an email %(payment)s cannot exceed 64 characters."
                        )
                        % {
                            "payment": line.payment_id.name,
                        }
                    )
        return res
