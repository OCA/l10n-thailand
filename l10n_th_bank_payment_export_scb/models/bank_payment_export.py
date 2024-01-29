# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


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

    def _get_wht_income_type(self, wht_line):
        wht_income_type = wht_line.wht_cert_income_type.lower()
        if len(wht_income_type) == 4:
            wht_income_type = "{}.{}".format(wht_income_type[:3], wht_income_type[3:])
        return wht_income_type

    def _get_rate_remittance(self):
        """Format rate to 3 digits integer and 7 digits decimal"""
        formatted_string = f"{self.scb_rate:.7f}"  # noqa: E231
        integer_part, decimal_part = formatted_string.split(".")
        # Ensure the integer part has exactly three digits
        integer_part = integer_part.zfill(3)
        return f"{integer_part}.{decimal_part}"

    def _get_total_amount_remittance(self):
        integer_part_total, decimal_part_total = str(self.total_amount).split(".")
        if len(decimal_part_total) < 2:
            decimal_part_total = decimal_part_total.zfill(2)
        return f"{integer_part_total}.{decimal_part_total}".zfill(17)

    def _get_receiver_address(self, object_address):
        receiver_address = super()._get_receiver_address(object_address)
        if self.bank == "SICOTHBK":
            if self.scb_product_code == "BNT" or self.scb_outward_remittance:
                receiver_address = object_address.street3 or "**street3 is not data**"
        return receiver_address

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
